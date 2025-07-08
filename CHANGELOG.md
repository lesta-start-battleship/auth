# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org).

---

## [1.1.5] - (2025-07-08)

### Fix

- fix(app): Fixing auth container initialization issue and updating dependencies

## [1.1.4] - (2025-07-08)

### Fix

- fix(app): Fixing the error in the kafka pod in auth-deployment.yaml file

## [1.1.3] - (2025-07-08)

### Fix

- fix(k8s): Fix secret name for auth-deployment.yaml file


## [1.1.2] - (2025-07-08)

### Fix

- fix(app): Adding loading to environment variables of private and public key for jwt tokens

## [1.1.1] - (2025-07-08)

### Fix

- fix(app): Remove check jwt tokens in ingress.yaml file and fix bug auth, working for user

## [1.1.0] - (2025-07-08)

### Feat

- feat(app): Adding admin panel


## [1.0.1] - (2025-07-07)

### Fix

- fix(app): Changing double quotes to single quotes in f-strings and adding dependencies to requirements.txt


## [1.0.0] - (2025-07-06)

### Feat

- feat(app): Change in registration logic

    - Added signals to intercept new user registration and send a letter to the specified email
    - Removed signals when registering and changing the username of the subsequent sending to the message queue
    - Added a unified function for adding a message broker message when registering and changing a username

- feat(containerization): Adding Kubernetes configuration
    
    - Deleted docker-compose and dockerfile
    - Added k8s configuration

- feat(jwt): Transition to **RS256 encryption keys**

### BREAKING CHANGE

- Now, when registering, a letter is send to the specified email, and when you click on the link, tokens are issued. Check api documentation for more details.

## [0.6.0] - (2025-07-04)

### Feat

- feat(app): Adding Orchestration and Containerization

    - Adding docker-compose and dockerfile
    - Adding missing files when switching to another branch


## [0.5.0] - (2025-07-03)

### Feat

- feat(app): Adding the ability to work with user currency

    - Adding currencies routes, services, schemas, models and views

- fix(app): Changing the response validation logic in the users and auth routes

## [0.4.2] - (2025-07-02)

### Fix

- fix(app): Adding signals when registering via Yandex and Google

## [0.4.1] - (2025-07-02)

### Feat

- feat(app): Add redirect to cli after successful google and Yandex auth

### Fix

- fix(app): Fix imports of models
- fix(app): Fix port number in main
- fix(app): Remove token check in cookies and unnecessary add-on when generating specification

## [0.3.0] - (2025-07-02)

### Feat

- feat(app): Adding signals

    - Adding signals for registration and change username

## [0.2.0] - (2025-07-02)

### Feat

- feat(app): Creating a Basic API

    - Creating an application structure (view, models, database, authorization using Google)

## [0.1.0] - (2025-06-25)

### Added
- Project structure
- Database tables and migrations

---
