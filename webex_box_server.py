from mindmeld.components import NaturalLanguageProcessor
from mindmeld.bot import WebexBotServer
from mindmeld import configure_logs

if __name__ == '__main__':
   # Create web hook here: https://developer.webex.com/docs/api/v1/webhooks/create-a-webhook
   WEBHOOK_ID = 'Y2lzY29zcGFyazovL3VzL1dFQkhPT0svNDAwNzI1ZDAtYWQ4ZC00ZDE4LTgyNGItZDdhNzJiOGNjOGI5'

   # Create bot access token here: https://developer.webex.com/my-apps/new
   ACCESS_TOKEN = 'MDBjYmQxNmQtMWU5Zi00YTVkLTlmZjMtYjFiMDFhNTJhNmY1YWQ4N2M2NWYtODdh_PF84_4fd62afc-068e-4c49-b7bf-3ef92e2f33f5'

   configure_logs()
   nlp = NaturalLanguageProcessor('.')
   nlp.build()

   server = WebexBotServer(name=__name__, app_path='.', nlp=nlp, webhook_id=WEBHOOK_ID,
                           access_token=ACCESS_TOKEN)

   port_number = 8080
   print('Running server on port {}...'.format(port_number))

   server.run(host='0.0.0.0', port=port_number)

