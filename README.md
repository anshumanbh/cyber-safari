# cyber-safari

![cyber-safari](./images/cybersafari.png)

## Prerequisites

```
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
```

`export OPENAI_API_KEY=<your-openai-api-key>`

## RAG Setup

```
python3 rag_setup.py
```
This will create a directory called `security_kb` with the vector database in your root directory.

## Running the Test Lab

```
python3 test_lab.py
```
This will start the test server locally on port 5000 serving the `main.js` file that has some vulnerabilities. It stores the application logs in the root directory under the directory `app_logs`.

You can verify this by sending some curl requests to the server such as:
```
curl http://localhost:5000/api/v1/profile
curl http://localhost:5000/api/v1/admin
curl http://localhost:5000/api/v1/user-info
```
Notice that they show up in the `app_logs/app.log` file.

## Running the Offensive Agent

```
python3 hack_agent.py
```
This will start the offensive agent that will try to exploit the vulnerabilities in the test server following the below steps:

![js-analyzer](./images/jsanalyzer.png)

## Running the Defensive Agent

```
python3 defense_agent.py
```
This will start the defensive agent that reads the application log file from `app_logs/app.log` and tries to recommend security controls based on security best practices available in the RAG system (that is in turn created from the security docs inside the `security_docs` directory). It follows the below steps:

![defense-agent](./images/defenseagent.png)
