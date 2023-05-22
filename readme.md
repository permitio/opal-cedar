# Authorization at Scale with Cedar and OPAL
## Why Authorization Should be Scale?
Recently, AWS unveiled Cedar, a new policy language.
Through this announcement, AWS provides compelling evidence that a reorganization is required for application-level authorization.
Rather than relying on imperative code within the application codebase to define policies, there is a need to transition towards a decentralized and declarative model, separate from the application code.

TBD comparison of imperative and delerative.

Separating policy from application code offers numerous advantages, with the primary one being the ability to develop scalable authorization. By employing declarative policy, permissions can be modified without the need for changes in the application code. This results in fewer bugs, quicker response times, and enhanced access control security. Furthermore, when implementing the same policy across multiple applications, the need to duplicate efforts and ensure synchronization becomes unnecessary.

In this article, we will use two open-source projects, Cedar and OPAL, to build a scalable authorization system. We will create a comprehensive solution that will let you write the policies, connect the decision engines to your data sources and keep it all up to date with all the policy configuration changes. By the end of this article, you'll have the full knowledge of building a complete authorization system - in open source - that is built to scale.

**This article required a local docker and git installation.**


## The Building Blocks of Modern Authorization System
Before we start to dirt our hands with code, let's take a zoom out to understand the building blocks of a modern application authorization system. By understanding the responsibility of each block, we will be able to separate the concern of each component. Making sure that we can scale our authorization system by its need without the fear of breaking it.

The modern authorization system consists of 5 components, Enforcement, Decision, Retrieval, Information, and Administration. Looking at the diagram below we can see that:

1. Admin configures the policy at the Retrieval point.
2. Developer configures data sources in the Information point.
3. Developer configures the Administration point to connect the data and policy to the Decision point.
4. Decision point deployed with the application to answer permissions decisions.
5. The application includes Enforcement points that allow or not allow users to perform operations.

![](arch_diagram.png)

Let's dive into each of the points, and see how should we separate their concern and build them to scale.


## Setup The Policy and Its Retrieval Point
To set up our retrieval point, we will use a Git repository. Of course, you can use any type of file system to write and maintain the policy files, but Git will help us to scale later with its built-in features like branching, version control, revisioning, and immutability.

For the purpose of the demo, we already created a repository that includes the whole configuration required for a complete authorization system. Let's start by cloning it to our local machine.

```
git clone git@github.com:permitio/opal-cedar.git
```

Taking a look at the repo we just clone, we can see two parts of our retrieval point. First, is a folder named Policy that represents our policy storage. Second, is the docker-compose file on our root folder that contains the configuration that creates a local git server that will serve our policy files. We used a local git server to avoid a redundant mess with SSH keys for real repositories. In the real world, you will probably use a remote git server like GitHub or GitLab.

Let's take a look at the folder named `policy` in our repository. As you can see there are 3 simple policy files, each consists policy permit statement for different roles of users.

admin.cedar
```
// Admins can perform any action on any resource
permit(
    principal in Role::"admin",
    action,
    resource
);
```

writer.cedar
```
// Writers can perform post and put on artciles
permit(
    principal in Role::"writer",
    action in [Action::"post", Action::"put"],
    resource in ResourceType::"article"
);
```

user.cedar
```
// All users can read all resources
permit(
    principal,
    action in Action::"get",
    resource
);
```

As we have done for the policy configuration, we can also configure the data sources for our application.


## Data Resources and Information Point
In the real world, the data sources for our application will be a database, identity management, or any other data source that will tell us more about the users and the data we're handling. For the purpose of the demo, we created a hard-coded JSON file that mocks our main app data source, including the resources, roles, and basic user details.

Let's take a look at the file named `data.json` in our data folder.
As you can find here, we represents our Roles, Resources, Actions, and Users, in hierarchical JSON format.
This format is the Cedar entity format, in a real app, we will use our DB to attribute our app data to the Cedar entities.

```
[
    {
        "attrs": {},
        "parents": [
            {
                "id": "admin",
                "type": "Role"
            }
        ],
        "uid": {
            "id": "admin@blog.app",
            "type": "User"
        }
    },
    {
        "attrs": {},
        "parents": [
            {
                "id": "writer",
                "type": "Role"
            }
        ],
        "uid": {
            "id": "senior_writer@blog.app",
            "type": "User"
        }
    },
    {
        "attrs": {},
        "parents": [
            {
                "id": "writer",
                "type": "Role"
            }
        ],
        "uid": {
            "id": "writer@blog.app",
            "type": "User"
        }
    },
    {
        "attrs": {},
        "parents": [
            {
                "id": "user",
                "type": "Role"
            }
        ],
        "uid": {
            "id": "user@blog.app",
            "type": "User"
        }
    },
    {
        "attrs": {},
        "parents": [],
        "uid": {
            "id": "article",
            "type": "ResourceType"
        }
    },
    {
        "attrs": {},
        "parents": [],
        "uid": {
            "id": "put",
            "type": "Action"
        }
    },
    {
        "attrs": {},
        "parents": [],
        "uid": {
            "id": "get",
            "type": "Action"
        }
    },
    {
        "attrs": {},
        "parents": [],
        "uid": {
            "id": "delete",
            "type": "Action"
        }
    },
    {
        "attrs": {},
        "parents": [],
        "uid": {
            "id": "post",
            "type": "Action"
        }
    },
    {
        "attrs": {},
        "parents": [],
        "uid": {
            "id": "article",
            "type": "ResourceType"
        }
    },
    {
        "attrs": {},
        "parents": [],
        "uid": {
            "id": "admin",
            "type": "Role"
        }
    },
    {
        "attrs": {},
        "parents": [],
        "uid": {
            "id": "writer",
            "type": "Role"
        }
    }
]
```

By using this data, we can get decisions in the policy like allow if user is writer or deny if user is reader.

As we configure our both control plane (policies) and data plane (data sources), we can now connect them together using the Administration point.

## Deploy the Policy Administration Point
Our administration point, OPAL, consists of two components, the OPAL server, and the OPAL client. The server is the part that tracks the changes in the policy and the data sources configuration and makes sure the client is up to date. The client, together with the configuration managed by the server, is responsible to make sure all data is updated and the decision point is ready to answer permissions decisions. The client is also running the policy agent itself, in our case, the Cedar agent. Our decision maker.

OPAL is configured as code and you can use any kind of IaC (such as Helm, TF, or docker) to set it up. In our case, we will use docker-compose to set up our OPAL server and client.

Let's take a look at the first services declared in the docker-compose file, where we compose the retrieval and information point. This is not a part of OPAL yet, just a way to set up everything needed to run OPAL in our demo

```
version: "3.8"
services:
  # A simple nginx server to serve our mock data sources.
  cedar_data_nginx:
      image: nginx:latest
      volumes:
        - "./data:/usr/share/nginx/html:ro"
  # Local git repo to host our policy.
  cedar_retrieval_repository:
      image: rockstorm/gitweb
      ports:
        - "80:80"
      volumes:
        - "../:/srv/git:ro"
```

The second part is OPAL itself, as you can see in the configuration, we point the OPAL server to track changes in our policy repository, the agent to be Cedar, and the data sources to be the server that serves the JSON file we created earlier.

```
  broadcast_channel:
    image: postgres:alpine
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
  opal_server:
    # by default we run opal-server from latest official image
    image: permitio/opal-server:latest
    environment:
      # the broadcast backbone uri used by opal server workers (see comments above for: broadcast_channel)
      - OPAL_BROADCAST_URI=postgres://postgres:postgres@broadcast_channel:5432/postgres
      # number of uvicorn workers to run inside the opal-server container
      - UVICORN_NUM_WORKERS=4
      # the git repo hosting our policy
      # - if this repo is not public, you can pass an ssh key via `OPAL_POLICY_REPO_SSH_KEY`)
      # - the repo we pass in this example is *public* and acts as an example repo with dummy rego policy
      # - for more info, see: https://docs.opal.ac/tutorials/track_a_git_repo
      - OPAL_POLICY_REPO_URL=http://cedar_retrieval_repository/opal-cedar/.git
      - OPAL_POLICY_REPO_MAIN_BRANCH=main
      # in this example we will use a polling interval of 30 seconds to check for new policy updates (git commits affecting the rego policy).
      # however, it is better to utilize a git *webhook* to trigger the server to check for changes only when the repo has new commits.
      # for more info see: https://docs.opal.ac/tutorials/track_a_git_repo
      - OPAL_POLICY_REPO_POLLING_INTERVAL=30
      # configures from where the opal client should initially fetch data (when it first goes up, after disconnection, etc).
      # the data sources represents from where the opal clients should get a "complete picture" of the data they need.
      # after the initial sources are fetched, the client will subscribe only to update notifications sent by the server.
      - OPAL_DATA_CONFIG_SOURCES={"config":{"entries":[{"url":"http://cedar_data_nginx/data.json","topics":["policy_data"],"dst_path":""},{"url":"http://cedar_data_nginx/data.json","topics":["policy_data"],"dst_path":""}]}}
      - OPAL_LOG_FORMAT_INCLUDE_PID=true

      # By default, the OPAL server looks for OPA rego files. Configure it to look for cedar files.
      - OPAL_FILTER_FILE_EXTENSIONS=.cedar
      - OPAL_POLICY_REPO_POLICY_EXTENSIONS=.cedar
    ports:
      # exposes opal server on the host machine, you can access the server at: http://localhost:7002
      - "7002:7002"
    depends_on:
      - broadcast_channel
  opal_client:
    # by default we run opal-client from latest official image
    image: permitio/opal-client-cedar:latest
    environment:
      - OPAL_SERVER_URL=http://opal_server:7002
      - OPAL_LOG_FORMAT_INCLUDE_PID=true
    ports:
      # exposes opal client on the host machine, you can access the client at: http://localhost:7000
      - "7766:7000"
      # you can access the Cedar agent APIs
      - "8180:8180"
    depends_on:
      - opal_server
    # this command is not necessary when deploying OPAL for real, it is simply a trick for dev environments
    # to make sure that opal-server is already up before starting the client.
    command: sh -c "exec ./wait-for.sh opal_server:7002 --timeout=20 -- ./start.sh"
    links:
      - cedar_data_nginx

volumes:
  opa_backup:
```  

Let's run this configuration to spin up our authorization system.

```
docker-compose up
```

Let's wait until OPAL finishes to set up everything and then we can start to use it.


## Use the Decision Point
One of the benefits of using administration points is the ability to auto-scale our decision points and manage them by OPAL client. If we look at the logs of the compose we ran, we can see that our cedar-agent is running on port 8180. We now have the option to call the decision APIs via REST and enforce the permissions in our application.

We can verify that our cedar-agent is up and running, returning the right decisions, by calling the `is_authorized` endpoint with the following requests.

```
curl -X POST "http://localhost:8180/v1/is_authorized" \
 -H "Accept: application/json" \
 -H "Content-Type: application/json" \
 -d '{"principal":"User::\"writer@blog.app\"","action":"Action::\"delete\"","resource":"Resource::\"article\""}' 
```

```
curl -X POST "http://localhost:8180/v1/is_authorized" \
 -H "Accept: application/json" \
 -H "Content-Type: application/json" \
 -d '{"principal":"User::\"writer@blog.app\"","action":"Action::\"post\"","resource":"Resource::\"article\""}' 
```

## Enforce Permissions
Since we configured a blog permissions mode, we also created a mock blog server, written in Node.js. Let's take a look at the file named server.js.

```
const express = require('express');
const app = express();
const bodyParser = require('body-parser');

app.use(bodyParser.json());

// Generic authorization middleware - Enforcement Point
const authorization = async (req, res, next) => {
    const { user } = req.headers;
    const { method, originalUrl, body } = req;

    // Call the authorization service (Decision Point)
    const response = await fetch('http://host.docker.internal:8180/v1/is_authorized', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        // The body of the request is the authorization request
        body: JSON.stringify({
            "principal": `User::\"${user}\"`,
            "action": `Action::\"${method.toLowerCase()}\"`,
            "resource": `ResourceType::\"${originalUrl.split('/')[1]}\"`,
            "context": body
        })
    });

    const { decision } = await response.json();

    // If the decision is not 'Allow', return a 403
    if (decision !== 'Allow') {
        res.status(403).send('Access Denied');
        return;
    }
    next();
};

// Mock routes
app.get('/article', authorization, async (req, res) => {
    const articles = ['article1', 'article2', 'article3'];
    res.send(articles);
});

app.post('/article/:id', authorization, async (req, res) => {
    res.send('Article created');
});

app.put('/article/:id', authorization, async (req, res) => {
    res.send('Article updated');
});

app.delete('/article/:id', authorization, async (req, res) => {
    res.send('Article deleted');
});

// Start the server
app.listen(3000, () => {
    console.log('Server running on port 3000');
});
```

To run this server, in another terminal window, run the following command to spin up our server.

```
docker-compose -f applications/node/docker-compose.yml up
```

We can now use CURL or Postman to verify our permissions model. Let's run the following two calls to see our authorization magic in action.

#### Allowed Request
```
curl -X POST http://localhost:3000/article/2 \
    -H 'Content-Type: application/json' \
    -H "user: writer@blog.app" \
```

#### Denied Request
```
curl -X POST http://localhost:3000/article/2 \
    -H 'Content-Type: application/json' \
    -H "user: user@blog.app" \
```

At this point, we have all our components up and running. As you saw, we separate all the components and verify that each of them is doing only one thing. Enforcement point, just enforce the permissions, decision point, just answer the permissions questions, and administration point, just connect the policy and data sources to the decision point. In the control plane, we just have policy and data source declarations.


## Enforce Permissions in Scale!
Now, that we are done with spin up our authorizaiton system, let's test the different scale aspects of our authorization system.


### Scale Enforcement
First, since we separated our policy configuration from our application, we can transparently add enforcement points in any other application we want. For example, here is a simple Python application that enforces the same permissions model we created earlier.

```
from functools import wraps

import requests
import os
from flask import Flask, request

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Authroization decorator middleware
def authorization(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = request.headers.get('user')
        method = request.method
        original_url = request.path

        # Call authorization service
        # In the request body, we pass the relevant request information
        response = requests.post('http://host.docker.internal:8180/v1/is_authorized', json={
            "principal": f"User::\"{user}\"",
            "action": f"Action::\"{method.lower()}\"",
            "resource": f"ResourceType::\"{original_url.split('/')[1]}\"",
            "context": request.json
        }, headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        decision = response.json().get('decision')

        # If the decision is not Allow, we return a 403
        if decision != 'Allow':
            return 'Access Denied', 403
        
        return f(*args, **kwargs)
    
    return decorated

# Mock endpoints
@app.route('/article')
@authorization
def get_articles():
    articles = ['article1', 'article2', 'article3']
    return {'articles': articles}

@app.route('/article/<id>', methods=['POST'])
@authorization
def create_article(id):
    return 'Article created'

@app.route('/article/<id>', methods=['PUT'])
@authorization
def update_article(id):
    return 'Article updated'

@app.route('/article/<id>', methods=['DELETE'])
@authorization
def delete_article(id):
    return 'Article deleted'

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3001))
    app.run(port=port, debug=True, host='0.0.0.0')
```

As you can see, no more imperative code is required to enforce the permissions, and streamline them on all our applications.

Let's run the application to see it in action.

```
docker-compose -f applications/python/docker-compose.yml up
```

Now, let's do the same CURL test we did earlier, but from the new application.

#### Allowed Request
```
curl -X POST http://localhost:3001/article/2 \
    -H 'Content-Type: application/json' \
    -H "user: writer@blog.app" \
```

#### Denied Request
```
curl -X POST http://localhost:3001/article/2 \
    -H 'Content-Type: application/json' \
    -H "user: user@blog.app" \
```

### Scale Permissions Model
A new feature request came, we want to allow writers to auto-publish their posts only if their account exceed 1000 karma points. In the imperative style permissions model, we would need to change the code in all our applications to add this new permission. In our case, we just need to edit the policy file in our policy repository.

In our `writer.cedar` file, let's add the following permission.
This permissions, will allow writers to post `published: true` articles only if their account has more than 1000 karma points.

```
permit(
    principal in Role::"writer",
    action in [Action::"post", Action::"put"],
    resource in ResourceType::"article"
) when { principal.karma > 1000 || (context has published  && context.published == false) }
```

As you can read in the policy, we added new permission that allow users to auto-publish their posts only if their account exists for more than 30 days. It is not only we can deliver our policy code without any application change, the declaration is much more readable and easy to understand.

### Scale Data Sources
Adding a policy is fine, but how would we know what is our writer karma?
For that, we may want to use external data sources that will tell us more about the user.
Do it in imperative style, we would need to change the code in all our applications to add this new data source.
In our case, we just need to add a new data source in our policy administration layer.

To save some time and reinitalization, we will just add the karma data in our main data source.
In real world, tho, we could use a different data source for each data type.

Let's add the karma data to our `data.json` file.
```
...
    {
        "attrs": {
            "karma": 2000
        },
        "parents": [
            {
                "id": "writer",
                "type": "Role"
            }
        ],
        "uid": {
            "id": "senior_writer@blog.app",
            "type": "User"
        }
    },
    {
        "attrs": {
            "karma": 500
        },
        "parents": [
            {
                "id": "writer",
                "type": "Role"
            }
        ],
        "uid": {
            "id": "writer@blog.app",
            "type": "User"
        }
    },
...
```

Let's run now the following CURL to see our new permission in action.

#### Allowed request
```
curl -X POST http://localhost:3001/article/2 \
    -H 'Content-Type: application/json' \
    -H "user: senior_writer@blog.app" \
    -d '{"published": true}'
```

#### Denied request
```
curl -X POST http://localhost:3001/article/2 \
    -H 'Content-Type: application/json' \
    -H "user: writer@blog.app" \
    -d '{"published": true}'
```

#### Allowed request with unpublished article
```
curl -X POST http://localhost:3001/article/2 \
    -H 'Content-Type: application/json' \
    -H "user: writer@blog.app" \
    -d '{"published": false}'
```

### Scale Decision Points
In this tutorial, we just use a local demonstration of OPAL running on local machine with `docker-compose` file, run all the components in the same machine.
In production, tho, you can use OPAL to scale your decision points as you need.
As we saw earlier, OPAL seperate the concern of the stateful servers, and stateless clients that running as sidecars in individual applications.
In OPAL repository, you can find helm charts and other instructions that will help you to deploy OPAL in production and scale it as your deployment needs.

## Conclusion
We just created a basic auto-scaled authorization system that can be used to enforce permissions in any application we want. We separated the control plane from the data plane and the enforcement plane. We also separated the policy configuration from the application code. We can now scale our system in any aspect we want, without changing the application code.

As the next steps of this learning path, you can take a look at OPAL and Cedar docs, and understand more how you can customize your needs with it for authorization in scale. We would also want to invite you to our Authorization slack community, hear your feedback and chat further on advanced use cases for application-level authorization.
