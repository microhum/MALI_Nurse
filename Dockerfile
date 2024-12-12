FROM python:3.10.9

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user . /app

EXPOSE 7826 8000 8001
# CMD python3 interface.py & \
#     uvicorn main:app --host 0.0.0.0 --port 8000 & \
#     uvicorn tts.tts:app --host 0.0.0.0 --port 8001

CMD python3 app.py
