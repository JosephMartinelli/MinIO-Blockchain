"""This module contains the implementation of lightweight nodes that are in essence client nodes in our application.
These nodes do not store a copy of the blockchain and if they want to commit any transactions they need to pass them to
full nodes/publishing nodes."""

from fastapi import APIRouter


router = APIRouter()
