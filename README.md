This guide will help you set up a Dockerized MySQL container along with a Flask application that connects to the MySQL database.

Steps to Set Up the Docker Environment
1. Pull the MySQL image 
	> docker pull mysql:8.0.40
2. Run the MySQL container
	> docker run --name mysql-db -e MYSQL_ROOT_PASSWORD=password -d mysql:version-8.0.40
3. Verify MySQL Container is Running
	> docker ps
4. Access the MySQL Container
	>  docker exec -it <CONTAINER-ID> /bin/bash
5. Access the MySQL Terminal
	> mysql -uroot -ppaasword
6. Create the Database.
	> create database TaskManagerDB
7. Create the tables.
8. Make the changes in the config.py file to update password and username.
9. Go to the directory where Dockerfile is present.
10. Build the Flask Application Docker Image
	> docker build -t task_manager_app_using_flask:latest .
11. Run the Flask Application Container
	> docker run -d -p 8010:8010 --name flask_mysql_app_container task_manager_app_using_flask 

Troubleshooting and Restarting the Containers
1. In case of any error, then fix it and restart the container
	> docker restart flask_mysql_app_container
2. To check the docker log
	> docker logs flask_mysql_app_container
