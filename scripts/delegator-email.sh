#!/bin/bash

TO="max@coaction.network"
SUBJECT="Delegator report"
MESSAGE=$(./delegator-report.sh)
mail -s "$SUBJECT" "$TO" <<< "$MESSAGE"
