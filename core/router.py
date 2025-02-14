#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter
from apps.image.routes import image_app_router
from core.conf import settings

route = APIRouter(prefix=settings.API_V1_STR)
route.include_router(image_app_router)
