#!/bin/sh

sudo journalctl -fu flask_app.service -n 200
