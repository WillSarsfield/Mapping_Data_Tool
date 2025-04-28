FROM python:3.9-slim

COPY requirements.txt requirements.txt
RUN pip install -U pip
RUN pip install -r requirements.txt

COPY . /app
WORKDIR /app

RUN mkdir ~/.streamlit
RUN mv config.toml ~/.streamlit/config.toml

ARG GOOGLE_ANALYTICS_ID
RUN if [ -n "$GOOGLE_ANALYTICS_ID" ] ; then \
    python add_ga.py --id $GOOGLE_ANALYTICS_ID ; \
  fi

ENTRYPOINT ["streamlit", "run"]

CMD ["Streamlit_Mapping.py"]
