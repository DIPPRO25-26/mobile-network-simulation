FROM python:3-alpine
WORKDIR /app
RUN apk add --no-cache py3-flask py3-gunicorn py3-flask-cors py3-requests
COPY . .
CMD ["gunicorn"  , "-b", "0.0.0.0:5000", "app:app"]
