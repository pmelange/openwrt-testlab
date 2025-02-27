# System Setup for labgrid

These instructions are adopted from [the labgrid documentation](https://labgrid.readthedocs.io/en/latest/getting_started.html#systemd-files).

* Clone the git repo for labgrid and openwrt-testlab
```
git clone https://github.com/pmelange/labgrid.git
git clone https://github.com/pmelange/openwrt-testlab.git
```

* Create the labgrid virtual environment
```
sudo python3 -m venv /opt/labgrid-venv
```

* Copy the exporter.yaml from the openwrt-testlab repo to /etc/labgrid

```
sudo mkdir /etc/labgrid
sudo cp openwrt-testlab/Documentation/RaspiOS/etc/labgrid/exporter.yaml /etc/labgrid
```

* To set up the labgrid user and group, copy the file ```labgrid/contrib/system/sysusers.d/labgrid.conf``` to ```/lib/sysusers.d/``` and run systemd-sysusers to apply the config.  A new system user "labgrid" and group "labgrid" will be created.

```
sudo cp labgrid/contrib/systemd/sysusers.d/labgrid.conf /lib/sysusers.d/
sudo systemd-sysusers
```

* Now that the user and group for labgrid have been created, modify the permissions of /opt/labgrid-venv to be owned by labgrid:labgrid.  Also add your user to the labgrid group

```
cd /opt
sudo chown -R labgrid:labgrid labgrid-venv
sudo chmod -R g+w labgrid-venv
sudo usermod -a -G labgrid pi   # change username as needed
sudo usermod -g labgrid pi      # optional to make labgrid the default group
```

* Log out and back in again so that your user is now a member of the labgrid group.

* From within the labgrid repo, change to the openwrt-testlab branch and install labgrid

```
cd ~/labgrid
git checkout openwrt-testlab
source /opt/labgrid-venv/bin/activate
pip install --upgrade pip
pip install .
```

* To set up the tempfiles needed for labgrid, copy the file ```labgrid/contrib/systemd/tmpfiles.d/labgrid.conf``` to ```/etc/tmpfiles.d```. The tempfiles listed in the config file will be created automatically by running ```systemd-tmpfiles --create```.

```
sudo cp labgrid/contrib/systemd/tmpfiles.d/labgrid.conf /etc/tmpfiles.d/
sudo systemd-tmpfiles --create
```

* set up the TFTP directory so that the labgrid group has write permissions

```
cd /srv
sudo chgrp labgrid tftp
sudo chmod g+w tftp
```

* Add the coordinator and exporter services to systemd by copying the files ```labgrid/conrib/systemd/labgrid*service``` to ```/etc/systemd/system``` and enabling the services.  Modify the service files as needed.  In this example, the labgrid-venv directory is located in /opt/labgrid-venv.  In addition, use ```systemctl edit labgrid-exporter.service``` as described in the labgrid documentation.

```
sudo cp labgrid/contrib/systemd/labgrid*service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl edit labgrid-exporter.service # make changes here
sudo systemctl enable labgrid-coordinator
sudo systemctl enable labgrid-exporter
sudo systemctl start labgrid-coordinator
sudo systemctl start labgrid-exporter
```

* Create the labgrid places with the script openwrt-testlab/Documentation/RaspiOS/create-places.sh.  Modify the file as necessary, such as the range in the for loop, depending on how many ports are on the system.

```
openwrt-testlab/Documentation/RaspiOS/create-places.sh
```

