# cyber-safari

![cyber-safari](./images/cybersafari.png)

## High Level Overview

![high-level-overview](./images/arch.png)

* There is an application server that has some vulnerabilities being served in a JavaScript file. The application logs all incoming requests.

* There is an offensive agent that tries to analyze the application's JavaScript file and exploit the vulnerabilities against some API endpoints.

* There is a RAG system that contains the security knowledge base i.e. the security controls required to defend against the vulnerabilities.

* There is a defensive agent that analyzes the application's logs and tries to propose security controls (retrieved from the RAG system) to defend against the vulnerabilities.

## Prerequisites

```
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
```

`export OPENAI_API_KEY=<your-openai-api-key>`

## Code Walkthrough

* `security_docs/` contains the security documents used to create the RAG system.
* `tools/` contains the tools used by the agents.
* `agents/` contains the agents.
* `rag_setup.py` contains the code to setup the RAG system.
* `test_lab.py` contains the code to start the test lab.


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
python -m agents.hack_agent
```
This will start the offensive agent that will try to exploit the vulnerabilities in the test server following the below steps:

![js-analyzer](./images/jsanalyzer.png)

## Running the Defensive Agent

```
python -m agents.defense_agent
```
This will start the defensive agent that reads the application log file from `app_logs/app.log` and tries to recommend security controls based on security best practices available in the RAG system (that is in turn created from the security docs inside the `security_docs` directory). It follows the below steps:

![defense-agent](./images/defenseagent.png)
