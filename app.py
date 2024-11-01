from flask import Flask, render_template, request, session
import pymysql
from werkzeug.utils import secure_filename 
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib
from sklearn import preprocessing

app = Flask(__name__)

app.secret_key = 'any random string'

def dbConnection():
    try:
        connection = pymysql.connect(host="localhost", user="root", password="root", database="spaceweather")
        return connection
    except:
        print("Something went wrong in database Connection")


def dbClose():
    try:
        dbConnection().close()
    except:
        print("Something went wrong in Close DB Connection")
                
con = dbConnection()
cursor = con.cursor()

model_filename1 = "static/models/KNN_Temp.joblib"
model_filename_Temp = joblib.load(model_filename1)

model_filename2 = "static/models/KNN_Wind.joblib"
model_filename_Wind = joblib.load(model_filename2)

def checkType(df):
    for column in df.columns:
        if df[column].dtype == 'object':
            if column in  ["Date","Time","Wind Dir","Hi Dir"]:
                continue
            print(column)
            df[column] = df[column].astype(float)
    return df

def dynamic_label_encode(df):
    encoded_df = df.copy()
    label_encoders = {}

    for column in df.select_dtypes(include=['object']).columns:
        print(column,df[column].dtype)
        le = preprocessing.LabelEncoder()
        encoded_df[column] = le.fit_transform(df[column])
        label_encoders[column] = le

    return encoded_df, label_encoders

@app.route('/')
def index1():
    return render_template('index.html') 

@app.route('/signup')
def signup():
    return render_template('signup.html') 

@app.route('/signin')
def signin():
    return render_template('signin.html') 

@app.route('/index')
def index():
    return render_template('index1.html') 

@app.route('/prediction')
def prediction():
    return render_template('prediction.html')

@app.route('/graph')
def graph():
    return render_template('graph.html')

@app.route("/checkRegister",methods=['POST','GET'])
def checkRegister():   
    if request.method == "POST": 
        details = request.form
        
        username = details['username']
        email = details['email']
        mobile = details['mobile']
        password = details['password']
        
        cursor.execute('SELECT * FROM register WHERE username = %s', (username))
        count = cursor.rowcount
        print(count)
        if count > 0: 
            return "fail"      
        else:
            sql1 = "INSERT INTO register(username,email,mobile,password)VALUES(%s,%s,%s,%s);"
            val1 = (username,email,mobile,password)
            cursor.execute(sql1,val1)
            con.commit()
            return "success"
        
@app.route('/SessionHandle',methods=['POST','GET'])
def SessionHandle():
    if request.method == "POST":
        details = request.form
        username = details['username']
        password = details['password']
        
        cursor.execute('SELECT * FROM register WHERE username = %s AND password = %s', (username,password))
        count = cursor.rowcount
        if count > 0:
            session['name'] = username
            return "success"
        else:
            return "fail" 
        
@app.route("/getPrediction",methods=['POST','GET'])
def getPrediction():
    if request.method == "POST":           
        file = request.files['filename']
       
        filename_secure = secure_filename(file.filename)
        file.save("static/uploadedfiles/"+filename_secure)
        
        df_train=pd.read_csv("static/uploadedfiles/"+filename_secure)
        newdf = checkType(df_train)        
        newdf['Temp Out'] = newdf['Temp Out'].astype(float)
        newdf['Hi Temp'] = newdf['Hi Temp'].astype(float)
        newdf['Dew Pt.'] = newdf['Dew Pt.'].astype(float)
        newdf['Wind Chill'] = newdf['Wind Chill'].astype(float)
        newdf['Solar Energy'] = newdf['Solar Energy'].astype(float)
        newdf['Heat Index'] = newdf['Heat Index'].astype(float)
        newdf['THW Index'] = newdf['THW Index'].astype(float)

        sample_data=pd.read_csv("static/dataset1.csv")
        
        df_train=pd.concat([newdf, sample_data])
        df_train=df_train.drop(['Unnamed: 0'], axis=1)

        a = checkType(df_train)
        encoded_df, label_encoders = dynamic_label_encode(a)
        
        df_mm = encoded_df.copy()
        for col in encoded_df.columns:
            if col == 'In Temp':
                continue
            mm = MinMaxScaler()
            df_mm[col] = mm.fit_transform(df_mm[[col]])
            
        new_predictions1 = model_filename_Temp.predict(df_mm[:1])
        new_predictions2 = model_filename_Wind.predict(df_mm[:1])
        
        print('-------------------------------')
        print(new_predictions1)
        print(new_predictions2)
        print('-------------------------------')
        
        return str(round(new_predictions1[0], 2))+'|'+str(round(new_predictions2[0], 2))
        
    return render_template('prediction.html')
        
 
if __name__ == "__main__":
    # app.run("0.0.0.0")    
    app.run(debug=True)