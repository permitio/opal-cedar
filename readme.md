# Authorization at Scale with Cedar and OPAL
## Why Authorization Should be Scale?
Lately, AWS announced a new policy language, Cedar. By its announcement, AWS shows an exciting proof that application-level authorization needs a refactor. Instead of using imperative code that defines policy in the application code, we should move to a declarative model, decentralized and separated from the application code.

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

Let's dive into each of the points, and see how should we separate their concern and build them to scale.


## Setup The Policy and Its Retrieval Point
To set up our retrieval point, we will use a Git repository. Of course, you can use any type of file system to write and maintain the policy files, but Git will help us to scale later with its built-in features like branching, version control, revisioning, and immutability.

For the purpose of the demo, we already created a repository that includes the whole configuration required for a complete authorization system. Let's start by cloning it to our local machine.

git clone TBD

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
In the real world, the data sources for our application will be a database, identity management, or any other data source that will tell us more about the users and the data we're handling. For the purpose of the demo, we created a hard-coded JSON file that mocks our data source, and the roles of our users.

Let's take a look at the file named users.json in our data folder.

```
TBD
```

By using this data, we can get decisions in the policy like allow if user is writer or deny if user is reader.

As we configure our both control plane (policies) and data plane (data sources), we can now connect them together using the Administration point.

## Deploy the Policy Administration Point
Our administration point, OPAL, consists of two components, the OPAL server, and the OPAL client. The server is the part that tracks the changes in the policy and the data sources configuration and makes sure the client is up to date. The client, together with the configuration managed by the server, is responsible to make sure all data is updated and the decision point is ready to answer permissions decisions. The client is also running the policy agent itself, in our case, the Cedar agent. Our decision maker.

OPAL is configured as code and you can use any kind of IaC (such as Helm, TF, or docker) to set it up. In our case, we will use docker-compose to set up our OPAL server and client.

Let's take a look at the first services declared in the docker-compose file, where we compose the retrieval and information point. This is not a part of OPAL yet, just a way to set up everything needed to run OPAL in our demo

```
TBD
```

The second part is OPAL itself, as you can see in the configuration, we point the OPAL server to track changes in our policy repository, the agent to be Cedar, and the data sources to be the server that serves the JSON file we created earlier.

```
TBD
```  

Let's run this configuration to spin up our authorization system.

```
docker-compose up
```

Let's wait until OPAL finishes to set up everything and then we can start to use it.


## Use the Decision Point
One of the benefits of using administration points is the ability to auto-scale our decision points and manage them by OPAL client. If we look at the logs of the compose we ran, we can see that our cedar-agent is running on port 7766. We now have the option to call the decision APIs via REST and enforce the permissions in our application.

We can verify that our cedar-agent is up and running by calling the `is_authorized` endpoint with the following request.

```
TBD
```

## Enforce Permissions
Since we configured a blog permissions mode, we also created a mock blog server, written in Node.js. Let's take a look at the file named server.js.

```
TBD
```

To run this server, in another terminal window, run the following command to spin up our server.

```
docker build -t blog-server .
docker run -p 3000:3000 blog-server
```

We can now use CURL or Postman to verify our permissions model. Let's run the following two calls to see our authorization magic in action.

```
TBD
```

You can also verify and audit the decisions made by the decision point by looking at the logs of the cedar-agent.

```
TBD
```

At this point, we have all our components up and running. As you saw, we separate all the components and verify that each of them is doing only one thing. Enforcement point, just enforce the permissions, decision point, just answer the permissions questions, and administration point, just connect the policy and data sources to the decision point. In the control plane, we just have policy and data source declarations.


## Enforce Permissions in Scale!
Now, that we are done with spin up our authorizaiton system, let's test the different scale aspects of our authorization system.


### Scale Enforcement
First, since we separated our policy configuration from our application, we can transparently add enforcement points in any other application we want. For example, here is a simple Python application that enforces the same permissions model we created earlier.

```
TBD
```

As you can see, no more imperative code is required to enforce the permissions, and streamline them on all our applications.

Let's run the application to see it in action.

```
docker build -t blog-client .
docker run -p 5000:5000 blog-client
```

Now, let's do the same CURL test we did earlier, but from the new application.

```
TBD
```

### Scale Permissions Model
A new feature request came, we want to allow users to auto-publish their posts only if their account exists for more than 30 days. In the imperative style permissions model, we would need to change the code in all our applications to add this new permission. In our case, we just need to change the policy file in our policy repository.

Let's add the following policy file to our policy repository.

```
TBD
```

As you can read in the policy, we added new permission that allow users to auto-publish their posts only if their account exists for more than 30 days. It is not only we can deliver our policy code without any application change, the declaration is much more readable and easy to understand.

### Scale Data Sources
Adding a policy is fine, but how would we know that a user exists for more than 30 days? For that, we may want to use external data sources that will tell us more about the user. Do it in imperative style, we would need to change the code in all our applications to add this new data source. In our case, we just need to add a new data source in our policy administration layer.

Let's mock a new service that will tell us how long the user exists.

```
TBD
```

And now, add it to our policy administration layer.

```
TBD
```

Let's run the following CURL to see our new permission in action.


### Scale Decision Points
TBD

## Conclusion
We just created a basic auto-scaled authorization system that can be used to enforce permissions in any application we want. We separated the control plane from the data plane and the enforcement plane. We also separated the policy configuration from the application code. We can now scale our system in any aspect we want, without changing the application code.

As the next steps of this learning path, you can take a look at OPAL and Cedar docs, and understand more how you can customize your needs with it for authorization in scale. We would also want to invite you to our Authorization slack community, hear your feedback and chat further on advanced use cases for application-level authorization.
