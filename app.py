#python web service for amica

import json
import base64
import pymongo
from bson import json_util
import pandas as pd, matplotlib.pyplot as plt, matplotlib.dates as mdates
import plotly, json
import plotly.graph_objects as go

dbclient = pymongo.MongoClient("mongodb://localhost:27017")
db = dbclient["amica_database"]
collection_auth = db["id_clients"]
collection_customer = db["customer"]	
collection_activity = db["activity_info"]
collection_total = db["total"]
collection_datatosync = db["data to sync"]

from flask import Flask
from flask import request
from flask import jsonify
from flask import render_template
from flask import send_file

app = Flask(__name__)

@app.route("/")
def home():
	return render_template('Home.html')
	

@app.route("/register")
def register():
	return render_template("sign_up.html")

@app.route("/accueil ")	
def accueil():
	return render_template('accueil.html')

@app.route("/auth/signup", methods=['POST'])
def auth_signup():
	base64_message = request.headers.get("Authorization").split(" ")[1]
	#print(base64_message)
	basic_auth = base64.b64decode(base64_message).decode("ascii")
	#print(basic_auth)
	name = basic_auth.split(":")[0]
	email = basic_auth.split(":")[1]
	password = basic_auth.split(":")[2]
	#print(name)
	#print(email)
	#print(password)
	
	signup_info = {'name':name, 'email':email, 'password':password}
	result = collection_auth.insert_one(signup_info)
	print(result)
	print(result.inserted_id)

	return jsonify('{"success":"true"}')
	
	
@app.route("/log_in")
def login():
	return render_template("log_in.html")

@app.route("/auth/login", methods=['POST'])
def auth_login():
	base64_message = request.headers.get("Authorization").split(" ")[1]
	#print(base64_message)
	basic_auth = base64.b64decode(base64_message).decode("ascii")
	#print(basic_auth)
	email = basic_auth.split(":")[0]
	password = basic_auth.split(":")[1]
	#print(email)
	#print(password)
	
	#check with the db
	query_find_user = {'email':email, 'password':password}
	match = collection_auth.find(query_find_user)
	print(match.count())
	if match.count() > 0:
		return jsonify('{"success":"true"}')
	else:
		return jsonify('{"success":"false"}')

#insert data into mongodb
@app.route("/postdata", methods=['POST'])
def postdata():
	get_collection_name = request.args.get('collection')
	content = request.get_json(silent=True)
	print(content)

	if get_collection_name == 'customer':
		collection_customer.insert_one(content)
	elif get_collection_name == 'activity':
		collection_activity.insert_one(content)
	else :
		collection_total.insert_one(content)
	
	return("request handled")

#data processing aka total
@app.route("/total")
def total():
	print("data processing ongoing")
	#data = collection_total.find_one({},{'_id': False})
	#print(json.loads(json_util.dumps(data)))
	#return json.loads(json_util.dumps(data))
	
	data = collection_datatosync.find_one({},{'_id': False})
	print(json.loads(json_util.dumps(data)))
	return json.loads(json_util.dumps(data))



@app.route("/dashboard/")
def dashboard():
	return render_template("d2.html")

@app.route("/weekly")
def weekly():
	#diagram sleep watch1
	sleepdf=pd.read_csv("/home/ubuntu/Desktop/amica.v2/data real life/data/withings data/watch2/sleep.csv")
	sleepdf['from']=pd.to_datetime(sleepdf['from'])
	sleepdf['to']=pd.to_datetime(sleepdf['to'])
	sleepdict={}
	for i,row in sleepdf.iterrows():
		sleepvalulist=[]
		date=str(row.loc['to'].day)
		lightsleep=row.loc['light']
		deepsleep=row.loc['deep']
		awakesleep=row.loc['awake']
		sleepvalulist.append(lightsleep)
		sleepvalulist.append(deepsleep)
		sleepvalulist.append(awakesleep)
		sleepdict[date]=sleepvalulist
	index=pd.date_range('15-12-2020','31-12-2020')
	sleepdfcomplete=pd.DataFrame()
	sleepdfcomplete['Date']=index
	for i,row in sleepdfcomplete.iterrows():
		if(str(row.loc['Date'].day) in sleepdict.keys()):
			sleepdfcomplete.loc[i,'light'] = sleepdict.get(str(row.loc['Date'].day))[0]
			sleepdfcomplete.loc[i,'deep'] = sleepdict.get(str(row.loc['Date'].day))[1]
			sleepdfcomplete.loc[i,'awake'] = sleepdict.get(str(row.loc['Date'].day))[2]
        
	sleepdfcomplete.index=sleepdfcomplete['Date']
	sleepdfcomplete.drop('Date', axis=1, inplace=True)
	sleepdfcomplete.fillna(0, inplace=True)
	for i,row in sleepdfcomplete.iterrows():
		if(row.loc['light']==0 and row.loc['deep']==0 and row.loc['awake']==0):
			sleepdfcomplete.loc[i,'Data Present'] = 'No'
		else:
			sleepdfcomplete.loc[i,'Data Present'] = 'Yes'
	print(sleepdfcomplete)
    
	trace_light=go.Bar(x=sleepdfcomplete.index, y=sleepdfcomplete.light, name='light sleep', marker=dict(color='#e73f22'))
	trace_deep=go.Bar(x=sleepdfcomplete.index, y=sleepdfcomplete.deep, name='deep sleep', marker=dict(color='#f6cb16'))
	trace_awake=go.Bar(x=sleepdfcomplete.index, y=sleepdfcomplete.awake, name='awake', marker=dict(color='#4CA66B'))
	layoutsleep=go.Layout(title="Sleep data", xaxis=dict(title="Date"), yaxis=dict(title="sleep amount"),)


	datasleep = [trace_light, trace_deep, trace_awake]
	figsleep=go.Figure(data=datasleep, layout=layoutsleep)
	graphJSONsleep = json.dumps(figsleep, cls=plotly.utils.PlotlyJSONEncoder)

	#activity

	combineddf_df = pd.read_csv("/home/ubuntu/Desktop/amica.v2/data real life/Combined_w2.xls")

	sorted_list=combineddf_df["calories_earned_value"].values.tolist()
	sorted_list.sort(reverse=True)
	top5vals=sorted_list[0:5]
	selected_df=combineddf_df.loc[combineddf_df['calories_earned_value'].isin(top5vals)]

	sorted_list=combineddf_df["calories_earned_value"].values.tolist()
	sorted_list.sort(reverse=True)
	top5vals=sorted_list[0:5]
	selected_df=combineddf_df.loc[combineddf_df['calories_earned_value'].isin(top5vals)]



	trace_calories_earned_value=go.Bar(x=combineddf_df.index, y=combineddf_df.calories_earned_value, name='light sleep', marker=dict(color='#e73f22'))
	

	layoutactivity=go.Layout(title="Daily Activity", xaxis=dict(title="Date"), yaxis=dict(title="Calories burnt"),)


	dataactivity = [trace_calories_earned_value]
	figactivity=go.Figure(data=dataactivity, layout=layoutactivity)
	graphJSONactivity = json.dumps(figactivity, cls=plotly.utils.PlotlyJSONEncoder)




	data={'plot':graphJSONsleep,
			'plot1':graphJSONactivity 
			}

	return render_template("statistics_w1.html", **data)

@app.route("/img")
def img():
	image_number = request.args.get('weekly')
	if image_number == "1":
		filename="./img/dp_weekly1.png"
	else:
		filename="./img/dp_weekly2.png"
	return send_file(filename, mimetype="image/png")


@app.route("/statistics2")
def statistics2():
	#diagram sleep watch2
	sleepdf=pd.read_csv("/home/ubuntu/Desktop/amica.v2/data real life/data/withings data/watch1/sleep.csv")
	sleepdf['from']=pd.to_datetime(sleepdf['from'])
	sleepdf['to']=pd.to_datetime(sleepdf['to'])
	sleepdict={}
	for i,row in sleepdf.iterrows():
		sleepvalulist=[]
		date=str(row.loc['to'].day)
		lightsleep=row.loc['light']
		deepsleep=row.loc['deep']
		awakesleep=row.loc['awake']
		sleepvalulist.append(lightsleep)
		sleepvalulist.append(deepsleep)
		sleepvalulist.append(awakesleep)
		sleepdict[date]=sleepvalulist
	index=pd.date_range('15-12-2020','31-12-2020')
	sleepdfcomplete=pd.DataFrame()
	sleepdfcomplete['Date']=index
	for i,row in sleepdfcomplete.iterrows():
		if(str(row.loc['Date'].day) in sleepdict.keys()):
			sleepdfcomplete.loc[i,'light'] = sleepdict.get(str(row.loc['Date'].day))[0]
			sleepdfcomplete.loc[i,'deep'] = sleepdict.get(str(row.loc['Date'].day))[1]
			sleepdfcomplete.loc[i,'awake'] = sleepdict.get(str(row.loc['Date'].day))[2]
        
	sleepdfcomplete.index=sleepdfcomplete['Date']
	sleepdfcomplete.drop('Date', axis=1, inplace=True)
	sleepdfcomplete.fillna(0, inplace=True)
	for i,row in sleepdfcomplete.iterrows():
		if(row.loc['light']==0 and row.loc['deep']==0 and row.loc['awake']==0):
			sleepdfcomplete.loc[i,'Data Present'] = 'No'
		else:
			sleepdfcomplete.loc[i,'Data Present'] = 'Yes'
	print(sleepdfcomplete)
    
	trace_light=go.Bar(x=sleepdfcomplete.index, y=sleepdfcomplete.light, name='light sleep', marker=dict(color='#e73f22'))
	trace_deep=go.Bar(x=sleepdfcomplete.index, y=sleepdfcomplete.deep, name='deep sleep', marker=dict(color='#f6cb16'))
	trace_awake=go.Bar(x=sleepdfcomplete.index, y=sleepdfcomplete.awake, name='awake', marker=dict(color='#4CA66B'))
	layoutsleep=go.Layout(title="Sleep data", xaxis=dict(title="Date"), yaxis=dict(title="sleep amount"),)


	datasleep = [trace_light, trace_deep, trace_awake]
	figsleep=go.Figure(data=datasleep, layout=layoutsleep)
	graphJSONsleep = json.dumps(figsleep, cls=plotly.utils.PlotlyJSONEncoder)

	#activity

	combineddf_df = pd.read_csv("/home/ubuntu/Desktop/amica.v2/data real life/Combined_w1.xls")

	sorted_list=combineddf_df["calories_earned_value"].values.tolist()
	sorted_list.sort(reverse=True)
	top5vals=sorted_list[0:5]
	selected_df=combineddf_df.loc[combineddf_df['calories_earned_value'].isin(top5vals)]

	sorted_list=combineddf_df["calories_earned_value"].values.tolist()
	sorted_list.sort(reverse=True)
	top5vals=sorted_list[0:5]
	selected_df=combineddf_df.loc[combineddf_df['calories_earned_value'].isin(top5vals)]



	trace_calories_earned_value=go.Bar(x=combineddf_df.index, y=combineddf_df.calories_earned_value, name='light sleep', marker=dict(color='#e73f22'))
	

	layoutactivity=go.Layout(title="Daily Activity", xaxis=dict(title="Date"), yaxis=dict(title="Calories burnt"),)


	dataactivity = [trace_calories_earned_value]
	figactivity=go.Figure(data=dataactivity, layout=layoutactivity)
	graphJSONactivity = json.dumps(figactivity, cls=plotly.utils.PlotlyJSONEncoder)




	data={'plot':graphJSONsleep,
			'plot1':graphJSONactivity 
			}

	return render_template("statistics_w2.html", **data)


#comparison_cal

@app.route("/Vs_friends")
def Vs_friends():


	watch1df=pd.read_csv("/home/ubuntu/Desktop/amica.v2/data real life/Combined_w1.xls")
	watch1df['Unnamed: 0'] = pd.to_datetime(watch1df['Unnamed: 0'], dayfirst = True)
	watch1df.rename(columns={'Unnamed: 0': 'Watch1_date'}, inplace=True)
	watch1df.rename(columns={'calories_earned_value': 'Watch1_cal'}, inplace=True)
	watch1df.rename(columns={'distance_walked_value': 'Watch1_distance'}, inplace=True)
	watch1df.rename(columns={'steps_taken_value': 'Watch1_steps'}, inplace=True)
	watch1df.index = watch1df ["Watch1_date"]
	watch1df.drop("Watch1_date",axis = 1, inplace = True)

	watch2df=pd.read_csv("/home/ubuntu/Desktop/amica.v2/data real life/Combined_w2.xls")
	watch2df['Unnamed: 0'] = pd.to_datetime(watch2df['Unnamed: 0'], dayfirst = True)
	watch2df.rename(columns={'Unnamed: 0': 'Watch2_date'}, inplace=True)
	watch2df.rename(columns={'calories_earned_value': 'Watch2_cal'}, inplace=True)
	watch2df.rename(columns={'distance_walked_value': 'Watch2_distance'}, inplace=True)
	watch2df.rename(columns={'steps_taken_value': 'Watch2_steps'}, inplace=True)
	watch2df.index = watch2df ["Watch2_date"]
	watch2df.drop("Watch2_date",axis = 1, inplace = True)

	combineddf= pd.concat([watch1df[['Watch1_cal','Watch1_distance','Watch1_steps']],watch2df[['Watch2_cal','Watch2_distance','Watch2_steps']]],axis =1, join = "inner")



	trace_Watch1_cal=go.Bar(x=combineddf.index, y=combineddf.Watch1_cal, name='Watch1_cal', marker=dict(color='#e73f22'))
	trace_Watch2_cal=go.Bar(x=combineddf.index, y=combineddf.Watch2_cal, name='Watch2_cal', marker=dict(color='#f6cb16'))
	
	
	layout_calorie_earned=go.Layout(title="Calories Burnt", xaxis=dict(title="Date"), yaxis=dict(title="Calories burnt"),)


	datacalorieearned = [trace_Watch1_cal, trace_Watch2_cal]
	figcalorieearned=go.Figure(data=datacalorieearned, layout=layout_calorie_earned)
	graphJSONcalorieearned = json.dumps(figcalorieearned, cls=plotly.utils.PlotlyJSONEncoder)

	




#comparison_steps

	trace_Watch1_steps=go.Bar(x=combineddf.index, y=combineddf.Watch1_steps, name='Watch1_steps', marker=dict(color='#e73f22'))
	trace_Watch2_steps=go.Bar(x=combineddf.index, y=combineddf.Watch2_steps, name='Watch2_steps', marker=dict(color='#f6cb16'))
	
	
	layoutsteps=go.Layout(title="No of steps", xaxis=dict(title="Date"), yaxis=dict(title="No of steps"),)


	datasteps = [trace_Watch1_steps, trace_Watch2_steps]
	figsteps=go.Figure(data=datasteps, layout=layoutsteps)
	graphJSONsteps = json.dumps(figsteps, cls=plotly.utils.PlotlyJSONEncoder)

	data={'plot1':graphJSONcalorieearned,
			'plot2':graphJSONsteps
			}


	return render_template("Vs_friends.html", **data)


#comparison_pie






if __name__ == '__main__':
	app.run(debug=True)
