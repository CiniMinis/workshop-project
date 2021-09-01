# The Genetwork Challenge
## The Challenge Story
Genetwork is a new up-and-coming social network which uses tiny DNA testers to generate a 'virtual DNA sequence' from it, which dictates your profile picture.

Raven Darkhölme is a wanted criminal who needs to face justice. The problem, is that she is a shape-shifter and can change her DNA sequence at will making it hard for us to track her. Raven is also a friend of the Genetwork developers and uses the service and, as far as we know, her virtual DNA on the website is up to date with her current form!

Unfortunately, her profile is marked as private which means her DNA is hidden. Your job, is to somehow leak her virtual DNA sequence and send it to us. Be careful! If you draw too much attention to your presence by attempting to find information about her avatar too many times, she will shapeshift!

## Setup
### Installations
1. Install [docker](https://docs.docker.com/get-docker/)
2. Install [docker-compose](https://docs.docker.com/compose/install/).
3. Clone the code from the [challenge repository](https://github.com/CiniMinis/workshop-project).

Make sure you have an up to date version which supports docker secrets.
### Configuring The Challenge
#### Security Parameters
The application has 4 primary secrets it uses. Be sure to change the content of these files accordingly in deployment for the challenge's security:
1. Change `flag.secret` to contain the flag for the challenge.
2. Change `database_password.secret` to contain a new, secure password for the database connection using URL-safe characters (placed in database URI)
3. Change `session_key.secret` and `medium_difficulty_key.secret` to contain secure 32 byte random cryptographic keys.
More details can be found in [Secret Values](#secret-values)
#### Deployment Parameters
The deployment can be configured using the `config.env` to set the DIFFICULTY parameter as specified in [Initialization Types](#initialization-types).
### Container Usage
#### Building
Run the command 
```bash
docker-compose build
```
#### Running
Run the command 
```bash
docker-compose up -d
```
Or for building and running combined use
```bash
docker-compose up -d --build
```
#### Shutting Down
```bash
docker-compose stop
```
Or for removing the containers too run
```bash
docker-compose down
```
### Connecting
The challenge server is now running on your machine. Connect to it at port 5000 to access the server!

### A Note About the TAU Nova server
The nova server seems to support opening ports, but currently it's docker-compose version is outdated.
I do not have permissions to update the docker-compose version there or properly install an updated version, and thus I could not test deployment on there.

If you wish to try it, use the TAU VPN to tunnel through the gate, follow these setup instructions on the Nova server and attempt to surf to it on port 5000 with your browser (surf to [http://nova.cs.tau.ac.il:5000](http://nova.cs.tau.ac.il:5000)). Hopefully this should work

---
From here on, the file has spoilers for the challenge!

Beware!
---

# Challenge Planning
This section details the theoretical background of the work in speculative execution attacks along with the rationale of incorporating these principles in the CTF challenge.

## The Design Problem
This CTF challenge was designed with the theme of cache side-channel attacks. One of the core reasons why caches are a prime target for side-channel attacks is that caches are a shared resource, thus external attackers can access the same cache used by the attack's victim.

This 'feature' of caches becomes a terrible issue when placed in a CTF environment; The fact caches are shared allows CTF participants to sabotage other players' cache maliciously or not.

To ensure participant isolation, more control over the cache is necessary - control which isn't really possible with hardware caches. Thus the challenge turned to software caches. Software caches are widely used throughout the web, and since they are based in software they can be built to isolate different players. In my searches, I found little-to-no discussion about the security implications of software caches so a challenge in which software caches goes awry seemed very interesting to me.

## Planning The Attack
A secondary advantage of using software caches, is the abstraction and simplification that can be achieved in software. For this reason, I tried finding a way to simplify a relatively complex cache-based attack and make it's core concept more accessible. Eventually, I settled on the idea of trying to create a software-[spectre](https://meltdownattack.com/) variant.

A common case of spectre utilizes speculative execution done in the CPU to load to the cache data to which the user can't access normally, and then leaking said data from the cache. If we strip away the element of branch predictions from the process, we are left with a case of executing some sort of 'authority check' in parallel to an action optimistically. In python form, the issue arises from code side effects when optimizing code of the form:
```python
if is_authenticated_to_do_something():
     result = do_something()
     return result
```
To the asynchronous form:
```python
is_authenticated, result = async.await(
    is_authenticated_to_do_something(),
    do_something()
)
if is_authenticated:
    return result
```

In the case of classic spectre, if the `do_something()` function is cached, secret values are leaked to the cache just like speculative execution.

The full details of the attack, are specified later.



# Server Design
The core design of the web-app utilizes the [Model-View-Controller design pattern](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller) as it's core approach. To it, an API segment was added, which is derived from the controllers pattern and handles dynamic Javascript calls from the server exclusively (ajax for example). This leads to a clearer purpose for the controllers, and separates API utilities from it.

Additionally, for then unique features required for the challenge, a modules folder was added which contains extensions and utilities for the server.

Finally, for the challenge-specific runtime data, a config folder (works as a python module) was created to define the app's parameters which correspond to the deployment setup and challenge difficulty.

Following is a detailed design reference for each specified element.

## Server Modules
This section describes the modules used by the server. This section specifies the gist of the modules and their key features.

### Avatar
As the name suggests, the avatar module defines and contains most of the avatar representation and utilities, including DNA/bitstring conversions, generating new body parts and attaching them to an avatar and so on. But an important distinction to make, is that the module only handles abstract representations and encoding/decoding - it is completely independent of the concrete assets used for part drawing in the front end.
The `avatar` module defines two important abstract base classes:
#### BodyPart
The BodyPart is the base class for any body part the avatar has. A class extending BodyPart must specify two properties:
* `VARIATIONS` - The amount of different shape variations the body part may have. The variation of instances is specified by a non-negative number smaller than the VARIATIONS parameter.
* `IS_COLORABLE` - A boolean. True if the body part has some sort of interior color which can be changed. In instances this color should be one of the 64 named colors specified in the `utils/color.py` module external to the app. If false, the body part cannot be recolored.

Each body part can be serialized to a bitstring and generated from a bitstring using the `to_bitstring` and `from_bitstring` methods respectively.
The encoding format for colorable body parts is a concatenation of the variation number encoded in bits and the index of the color in the color utilities list encoded in bits, where each encoded number is zero-filled to take up the full potential length possible for the number. For non-colorable body parts, the color index is omitted.

For example, for a colorable body part with 6 variations, the part with variation 2 and color 'darkslategray' (index 63) is `010111111`.

#### AvatarBase
This is the base class of all Avatars. An avatar class is characterized by a list of body parts registered to it.
Part registration is done using the `register_part` class decorator. Each avatar instance contains instances of the body parts it contains which defines it's look.

An avatar can be serialized and deserialized to a bitstring similarly to body parts. The encoding of an avatar to bits, is simply the concatenation of the bitstring encodings of each body part is has. Using this bitstring, the DNA sequence can be defined. DNA nucleotides (the characters C, G, A, and T which form DNA sequences) are mapped to bit pairs (C='00', G='01', and so on) and then a DNA encoding of an avatar is done by left-padding the avatar's bitstring to an even length with zeroes (so that the string can be evenly split into 2 bit pairs) and then giving each 2-bit chunk the matching nucleotide.

For example, the previous example's bit encoding `010111111` is filled to an even length (`0010111111`) and mapped to `CATTT`.
DNA conversions are supported directly for avatars using `to_dna` and `from_dna` serializers.

### Session Manager
The `session_manager` module, defines an event based framework for handling clients connecting to the challenge server.
Sessions are identified by a uuid specified in the flask-session data and are used as identifiers for solution attempts.
Additionally, the module optionally creates a garbage-collector for inactive sessions, which removes sessions which did not send any requests in a specified time window. 

The module defines three event types:
* Create - triggered when a session is 'new', and automatically triggered for requests which have no session id or the garbage-collector removed the given session id (the session needs to be recreated).
* Connect - triggered when a request arrives with an established session id.
* Delete - triggered by the garbage collector for session-ids it removes.

A `SessionHandler` instance can be used to access this framework, by defining event handlers (with special decorators) and accessing the current session id running.

### User Cache
The user cache modules defines multiple variations of function caches for each server client, i.e. each client gets a unique cache which isn't altered by other clients' requests to the server. This is critical for a CTF challenge server where other contestants may send many requests to the server and each user's cache should not be changed. Existing function caching solutions (as far as I managed to find) are server-wide caches, which usually aim to optimize very popular pages or ver common calculations for **all users**. This module allows ctf contestants to control the cache with which they are playing without any worries of external corruption.

The three solutions are also the defining feature of this challenge and are the changing variable between different challenge difficulties. The solutions are summarized in the following table:
| name | difficulty | description | size | is safe for parallel requests? | data leakage and attacks |
|------|------------|-------------|------|--------------------------------|--------------------------|
| `LRUSessionCache` | Easy | A flask-sessions based LRU cache. The cache is a dictionary which maps function parameters to the last access time and the calculation result for these parameters| 10 | **No**. [The entirety of flask-sessions doesn't support this.](https://github.com/fengsp/flask-session/issues/71) (not only cookies are the issue) | Since the cache is stored in the cookie, by saving the cookie with an empty cache, complete cache flushes are possible. Additionally, flask-sessions are not encrypted, thus the entire cache dict can be read. |
| `AesLRUSessionCache` | Medium | An extension of the `LRUSessionCache` which encrypts the cached function inputs and outputs with AES. | 10 | **No**. [The entirety of flask-sessions doesn't support this.](https://github.com/fengsp/flask-session/issues/71) (not only cookies are the issue) | The same cache flush from the Easy cache is possible. Cached values can't be read directly, but the dictionary shape reveals the size of the cache. If after a call no values were cached, it means the value was already in the cache. |
| `SqlLRUSessionCache` | Hard | A [SessionHandler](#session-manager) based solution which saves all cache records in an SQL database on the server side. | 64 | **Yes!** (as far as I know, issues can be fixed) | Since the user has no direct access to the cache and no direct view of it, only the effects of the cache can be observed. Primarily, when the server responds faster than normal, it indicates that the value was cached and the function wasn't calculated. |

####

## Initialization and Configuration
The initialization utilizes a `create_app()` function - a factory for making the app with the correct configuration.

Since most web-app platforms utilize multiple worker processes for the application deployment, it is important that the configurations of different processes will be created identically.
To achieve this, the configuration specification (difficulty and deployment type) is specified by either exact values passed to the factory or environment variables (`DIFFICULTY` and `DEPLOYMENT_TYPE` respectively) The complete configuration of the app is generated by the `AppConfigFactory` class, which takes a difficulty and deploy_type parameters as described, and makes an configuration object which contains both the deployment and difficulty configurations specified.

### Initialization Types
The app configuration utilizes two independent parameters, `deploy_type` and `difficulty`.
The deploy_type specifies the code execution mode used by the app, primarily where databases are defined, the cookie signing keys, and treatment of exceptions (displays in debug). It has three possible types:
* **Development** - runs the app in [Flask debug mode](https://flask.palletsprojects.com/en/2.0.x/config/#DEBUG), and uses local sqlite databases in an expected `instance` subfolder of the server. String aliases (recognized names by the config): `dev`, `development`.
* **Testing** - runs the app in [Flask testing mode](https://flask.palletsprojects.com/en/2.0.x/config/#TESTING). and uses the same local databases as development. String aliases: `test`, `Testing`.
* **Production** - runs the app normally. If a `DB_PASSWORD_FILE` environment variable is defined, it treats it's contents as a password for a database user 'genetwork' and uses a remote PostgreSQL server with an expected host `db` for the database. These values are the setup used in the app containerization. If the environnement variable is missing, it falls back to using local sqlite databases with the same path as development but a different users database. This is the default deployment type, and has string aliases: `prod`, `production`, `ctf`, `challenge`.

The difficulty option controls the challenge's difficulty by changing the caching type the server uses. The possibilities for the difficulty are easy (aliases `easy`, `flask`, `cookie`), medium (aliases `medium`, `normal`, `encrypt`, `encrypted`, `aes`), and hard (aliases `sql`, `sqlalchemy`, `hard`).
For more details, see the user_cache module.

### Secret Values
There are 4 values which directly impact the challenge's security. Hence, to properly secure them, there are 4 `*.secret` files which are loaded in the dockerization of the challenge automatically as [docker secrets](https://docs.docker.com/engine/swarm/secrets/) and should contain secure values. Any time the server attempts to use these values, it tries to fetch them from corresponding files specified in environment variables (see docker secrets) and if the environnement variables are missing, the server falls back to some default. These are:

|secret file|environnement variable|description|fallback behavior|
|-----------|---------------------|-----------|-----------------|
|`flag.secret`|`CTF_FLAG_FILE`|The flag given for beating the challenge|Tries to import a variable `FLAG` from a python module named `instance` in the server folder|
|`session_key.secret`|`SESSION_KEY_FILE`|The signing key used by flask for signing session cookies|Randomly generate a key. If many processes are used in the deployment, their keys may be inconsistent!|
|`database_password.secret`|`DB_PASSWORD_FILE`|In production deployment, uses the password to log in to a remote PostgreSQL server. Full behavior is defined in production initialization|Use a local sqlite server server|
|`medium_difficulty_key.secret`|`AES_SESSION_KEY_FILE`|The AES key used by the AesLRUSessionCache (medium difficulty caching)|Randomly generate a key. If many processes are used in the deployment, their keys may be inconsistent!|

### Avatar Configuration
The config module also contains an avatar sub-module which defines the avatar class used by the server for all avatar related management and specifies the avatars body parts and their properties.

## Core App Design
This section specifies the design of the core application - the models, views, controllers and api python modules.
### Models
The models are the core database tables used in the web-app.

The primary model used is the User table. This represents regular users in the genetwork application (not Raven, which needs to be attacked).
Users contain the following columns:
* **user_id** - unique number identifying the user.
* **dna** - the DNA string of the user's avatar.
* **is_private** - boolean, if True the user's DNA is not publicly shown.
* **name**, **location**, and **job** (3 separate columns)- the name, location, and job of the user. Used for variety in user profiles, and not always listed (except for name).
Additionally, a factory object, `UserFactory`, was designed to generate fake users including realistic names, locations and jobs ([using Faker](https://faker.readthedocs.io/en/master/)).

The actual 'users' which are being attacked in the challenge are named Villains, and are stored in the `Villain` model. These models are generated for each session creation, which ensures players get different villains and players don't interfere with each others villains. The Villain model, has few fields in common with User model. Villain has three columns:
* **ssid** - the session id to which the villain belongs.
* **dna** - the *current* dna of the villain (they shapeshift).
* **detections** - the number of queries to get DNA data about the villain which were made (since last shapeshift).
The villains also shapeshift if the number of detections get too high (over 256), which changes the villain's DNA and resets the detection counter.

To make the Villain model attacked match the User model for static models two features exist:
1. The Villain model can return 'fake columns' - literal (constant) columns which give all villains the same value. This is used to replace all values which a user would have but a villain wouldn't.
2. A `SessionUsers` class was made, with a unique meta-class which gives it a fake `query` attribute used by flask-sqlalchemy. This fake attribute, turns queries made to this object query a table with all User instances in it, and adds to it the Villain which belongs to the currently running session. This completely abstracts away the fact the villain is not a real user. 

### API
The implemented API has 3 main calls. The get-user-deck call, which sends formatted html snippets of users for loading new users in the explore view will be emitted in this overview, since it is relatively small and mostly relates to the front-end.
The primary two API functions, `part_from_dna` and `part_from_users` are both JSON based and are the core of the challenge's vulnerability, along with the `part_to_dict` utility function. Functions are converted to match a uniform JSON-based API and return error cleanly to the Javascript using a special decorator for reformatting the outputs.

#### part_to_dict
This is the main source of the vulnerability, as it is a utility function used by both primary API functions. This function is cached using a [user cache](#user-cache) which matches the difficulty.
The function takes a [body part](#bodypart) and converts it to a dictionary of drawing instructions, such as the assets which represent the part's shape and the color of the part. The function also validates that the asset files exist, which gives it a non-negligible running time (for hard difficulty).

The function of this cache is attacked in every difficulty with a similar theme.

#### part_from_dna
This is a simple API call parses a DNA sequence and returns the part_to_dict drawing instructions for one of the parts in the DNA.
In the normal flow of the website it isn't heavily used, but for the attacks it is critical since it allows the attacker to cache arbitrary parts since part_to_dict is called with the part decoded from the DNA sequence (which is attacker controlled).

#### part_from_user
This API call returns part_to_dict drawing instructions for a user's body part. This is by-far the most common API call in the website, and as such optimizing this function can be very effective. Specifically, this function asynchronously calculates:
1. `is_user_visible`: The check if the user is private (and the villain detection count update if needed)
2. `fetch_part_from_user`: the query for the user's DNA and the potentially slow (if a cache miss occurred) `part_to_dict` call

This effectively means that the `part_to_dict` function is speculatively called. Instead of a code flow like:
```python
if is_user_visible(user):
    return fetch_part_from_user(user, requested_body_part)
````
It is executed optimistically, in parallel. As it did with the Spectre vulnerabilities, this optimistic execution leaks sensitive data (the parts a private user) to the cache. What remains is leaking the sensitive data from the cache.

### Controllers, Views, and UI
Since the api logic was separated from the controllers, the controllers and views both serve the user interface and website flow almost entirely.
The controllers are primarily a link between the HTTP requests and the views, which are entirely frontend elements. The controllers primarily define the routing rules for all the paging views (the paths within the website) and at most query users for displaying their data on pages.

All the dynamic drawing of avatars is done using Javascript and queries to the API instead of on the server side (offloading work).

The views utilize [the Jinja template engine](https://jinja.palletsprojects.com/en/3.0.x/) for organization (template inheritance) and dynamic data loading (formatting data from the server into the returned webpage). Additionally, the websites visuals utilize [Bootstrapping](https://getbootstrap.com/) in addition to the html, css and javascript to simplify web design.

# Solving The Challenge
**Note:** The challenge should show the code main API code and the relevant user cache. Otherwise there is no way to know the speculative execution exists. Choosing how much code to show is left for the CTF admins to decide, but note that showing how the difficulties change gives a massive hint.

## The Attack
The main vulnerability's concept (the leak to cache) was described in the [Planning The Attack section](#planning-the-attack), and the specific manifestation of it in the website was described in the (API section)[#api]. Additionally, the potential attack for each user cache were described in the [User Cache section](#user-cache).

To put it all together, assuming all steps of the attack work as described, the API vulnerability is used to leak a body part of the target user's to the attacker's cache. Then, the attack against the user cache which matches the challenge's difficulty is used to leak the body part from the cache.
This way, we can leak the villain's DNA part by part (pun intended).

Here is an example of a flow based on the attack method, in the `attack_utils.py` solution file:
```python
user_bitstring = ""
for part in BODY_PARTS:
    part_bits = attacker.find_part(part)
    user_bitstring += part_bits
user_dna = bitstring_to_dna(user_bitstring)
return user_dna
```

## Solution Scripts
The solution scripts subdirectory in the repository has 3 example solutions, one for each difficulty.
All three are based on the Attacker defined in the `attack_utils`. When hosting this challenge, you may consider giving the attack_utils script or parts of it to your players to simplify the scripting. Alternatively, you could allow them to use the [avatar module](#avatar) to allow them to save on implementations of utilities such as bitstring to DNA conversions and constants for the bit-length of each body part. These are considerations for the CTF administrators.

### Setting the Solution Scripts Up
Simply install the requirements from the solution scripts subdirectory with:
```bash
pip install -r requirements.txt
```

### Running the Solution Scripts Directly
Simply running the solution script of the relevant difficulty in python, will execute a verbose attack on the user with id 666 (the default for the Villain) and will assume the server runs at `http://127.0.0.1:5000`. You may want to examine the different configurations for the attacker in the constructor (documented in the class attributes at the class definition) and specify these selections in the call to the `Attacker.attack` method.

### Using the Attacker Object
Alternatively, you may explore the attackers and the attack possibilities using the attacker objects directly. Simply import the attacker type you would like to any python file and use the file as a library documented in these files.

---
Note: The hard difficulty attacker is, as mentioned prior, a timing based attacker. Currently it is configured to run a very fast attack which is reliable on my setup. Depending on your setup, you may need to alters the reps parameter. 