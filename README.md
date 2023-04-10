# rent-docker

To be able to develope on various machines with the same env we are using docker. The submodules can be used independently


# Install and run dev
1. `git clone --recurse-submodules git@github.com:rwth-medialab/rent-docker.git`
2. `docker-compose -f docker-compose.dev.yml build`
3. `docker-compose -f docker-compose.dev.yml up`
4. open [localhost:3000](http://localhost:3000)

# init backend
1. `python manage.py makemigrations`
2. `python manage.py migrate`
3. `python manage.py createsuperuser`
