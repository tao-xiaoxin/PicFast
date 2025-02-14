#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter
from apps.image.routes import image_router
from core.conf import settings

routers = APIRouter(prefix=settings.API_V1_STR)
routers.include_router(image_router)
