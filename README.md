# Yangify

Yangify is a framework that allows you to easily write code that can map structured and unstructured data into data modelled using YANG models. Yangify can also do the opposite operation and convert data modelled with YANG models into other structured or non-structured data. This allows you to easily write code that can parse native output/data/configuration from network devices and map them into YANG models and vice-versa.

## Installing yangify

You can install yangify with pip:

```
pip install yangify
```

## Ways to Get Started with Yangify


* [Start Executing Juptyer Notebooks](#Start-Executing-Juptyer-Notebooks)
* [Go Right into a Working Yangify Dev Environment](#Go-Right-into-a-Working-Yangify-Dev-Environment)
* [Read the Docs](https://yangify.readthedocs.io)


### Start Executing Yangify Juptyer Notebooks

**Step 1**

Clone the repository:


```
$ git clone https://github.com/networktocode/yangify
```


**Step 2**

Navigate into `yangify`:


```
$ cd yangify
```


**Step 3**

Build the containers needed.


```
$ make build_test_containers
```

**Step 4**

Start a container so you can run Jupyter notebooks:


```
make dev_jupyter
```

**Step 5**

Launch a browser and navigate to the following URL:

```
http://127.0.0.1:8888
```


You will find all of the notebooks in `docs/tutorials` and also `docs/tutorials/parsing-quickstart`.

These same notebooks can be viewed without being interactive in the Read the Docs.



### Go Right into a Working Yangify Dev Environment

> Note: this dev environment is built for parsing.

**Step 1**

Clone the repository:


```
$ git clone https://github.com/networktocode/yangify
```


**Step 2**

Navigate into `yangify`:


```
$ cd yangify
```


**Step 3**

Build the containers needed.


```
$ make build_test_containers
```


**Step 4**

Create a container that you'll use for development & testing. This container will get built such that you can modify files in your local directory and execute them within the container environment.  Great for using your local text editor and executing in pre-buit enviornment.


```
make enter_dev_container
```

This will drop you right into the container.


**Step 5**

Install `yangify` with `make install`:

```
root@e726de8f2226:/yangify# make install
poetry install
Skipping virtualenv creation, as specified in config file.
Installing dependencies from lock file

Nothing to install or update

  - Installing yangify (0.1.0)
A setup.py file already exists. Using it.
root@e726de8f2226:/yangify#
```


**Step 6**

Navigate into the `parsing-quickstart` directory (inside the container):


```
root@e726de8f2226:/yangify# cd docs/tutorials/parsing-quickstart/
root@e726de8f2226:/yangify/docs/tutorials/parsing-quickstart#
```

**Step 7**


Try out the `dev-yangify.py` script:


```
root@e726de8f2226:/yangify/docs/tutorials/parsing-quickstart# python dev-yangify.py --vlans
{
    "openconfig-vlan:vlans": {
        "vlan": [
            {
                "vlan-id": 10,
                "config": {
                    "vlan-id": 10,
                    "status": "ACTIVE"
                }
            },
            {
                "vlan-id": 20,
                "config": {
                    "vlan-id": 20,
                    "name": "web_vlan",
                    "status": "ACTIVE"
                }
            },
            {
                "vlan-id": 30,
                "config": {
                    "vlan-id": 30,
                    "name": "test_vlan",
                    "status": "ACTIVE"
                }
            }
        ]
    }
}
root@e726de8f2226:/yangify/docs/tutorials/parsing-quickstart#
```
