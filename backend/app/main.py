from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from time import perf_counter

from starlette.requests import Request

from app.api.v1 import attendance, auth, dashboard, intelligence, notifications, reports
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.bootstrap import bootstrap_initial_admin, bootstrap_local_role_users, bootstrap_rbac
from app.services.observability import api_metrics_collector
from app.services.startup import assert_database_ready

app = FastAPI(
    title='TFI Internship Operations & Analytics API',
    version='0.1.0',
    description='Backend for the TFI internship operations and analytics platform.',
)

allowed_hosts = [host.strip() for host in settings.allowed_hosts.split(',') if host.strip()]
if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

app.add_middleware(
    CORSMiddleware,
    # Normalize frontend origins: accept comma-separated string or list.
    allow_origins=(settings.frontend_origins
                   if isinstance(settings.frontend_origins, list)
                   else [o.strip() for o in settings.frontend_origins.split(',') if o.strip()]),
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.middleware('http')
async def add_security_headers(request: Request, call_next):
    started_at = perf_counter()
    response = await call_next(request)
    api_metrics_collector.record((perf_counter() - started_at) * 1000, response.status_code)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    return response

app.include_router(auth.router, prefix='/api/v1/auth', tags=['auth'])
app.include_router(dashboard.router, prefix='/api/v1/dashboard', tags=['dashboard'])
app.include_router(attendance.router, prefix='/api/v1/attendance', tags=['attendance'])
app.include_router(reports.router, prefix='/api/v1/reports', tags=['reports'])
app.include_router(intelligence.router, prefix='/api/v1/intelligence', tags=['intelligence'])
app.include_router(notifications.router, prefix='/api/v1/notifications', tags=['notifications'])

@app.on_event('startup')
def startup_bootstrap():
    with SessionLocal() as session:
        assert_database_ready(session)
        bootstrap_rbac(session)
        bootstrap_initial_admin(session)
        bootstrap_local_role_users(session)

@app.get('/')
def root():
    return {'status': 'ok', 'app': 'TFI API'}
