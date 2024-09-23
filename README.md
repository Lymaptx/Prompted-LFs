# Prompted-LFs

## Getting Started

### Environments Set-up

#### Python >= 3.9

*We suggest use virtual environment to avoid messing up your own environments.*

~~~sh
$ pip install -r ./backend/requirements.txt
~~~

#### NPM >= 7 

~~~sh
$ cd ./dashboard
$ npm install
~~~
### Wrench Datset
Our tool is highly dependent on the Wrench dataset, which can be accessed from the following link:
[https://github.com/JieyuZ2/wrench](https://github.com/JieyuZ2/wrench). 

### OpenAI API
The data set file downloaded should be placed within `wrench`. Our system needs to access the GPT-4o API, so the api_key in `app.py` should be replaced by our own API key.The application URL is below: 
[https://openai.com/api/](https://openai.com/api/)

### Basic Usage

#### Start backend

~~~sh
$ cd ./backend
$ python app.py
~~~

#### Quick start

~~~sh
$ npm run dev
~~~
Copy the url and open it in browser.

