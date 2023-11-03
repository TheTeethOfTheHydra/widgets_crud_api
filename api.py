import tornado.web
import json
import http
import re
import logging
from models import Widget
from datetime import datetime
from users import User

logger = logging.getLogger("my_logger")


def widget_to_dict(widget):
    """
    This method converts a Widget object from peewee into a dictionary

    Args:
      widget (models.Widget): A peewee Widget object holding data
      corresponding to a database record for a widget

    Returns:
      a dictionary containing the database record values for a Widget

    """

    return {
        'id': widget.id,
        'name': widget.name,
        'parts': widget.parts,
        'last_user': widget.last_user,
        'created_date': widget.created_date.isoformat(),
        'updated_date': widget.updated_date.isoformat()
    }


def validate_widget_data(request_body):
    """
    This method checks the request_body of a received HTTP request to
    make sure it contains the required data and the data formatting rules
    have been met before attempting a write to the database

    Args:
      request_body (tornado request body): the request body for a received HTTP
      request

    Returns:
      http response code (int): indicates the outcome of the validation
      http response message (str): a message to explain the outcome
      widget_data (dictionary): the valid name and parts fields for a
      widget that the request has submitted for a write operation to the
      database

    """

    try:
        widget_data = json.loads(request_body)

        if set(widget_data.keys()) != {"name", "parts"}:
            return http.HTTPStatus.UNPROCESSABLE_ENTITY,
            "The json provided does not contain the correct keys \
            for the requested operation.",
            widget_data

        name = widget_data["name"]
        if not (isinstance(name, str) and len(name) <= 64
                and re.match(r'^[A-Za-z0-9 _-]*$', name)):
            return http.HTTPStatus.UNPROCESSABLE_ENTITY,
            "The widget 'name' should be a UTF-8 string of 64 characters \
            or less.",
            widget_data

        parts = widget_data["parts"]
        if not (isinstance(parts, int) and parts >= 0):
            return http.HTTPStatus.UNPROCESSABLE_ENTITY,
            "The widget 'parts' should be a non-negative integer.",
            widget_data

        return http.HTTPStatus.OK, "Validation successful.", widget_data

    except json.decoder.JSONDecodeError:
        return http.HTTPStatus.BAD_REQUEST,
        "The data provided is not valid JSON.",
        {}


class WidgetHandler(tornado.web.RequestHandler):
    def check_api_key(self):
        api_key = self.request.headers.get('X-API-Key')
        try:
            api_user = User.get(User.api_key == api_key)
            self.current_user = str(api_user.name)
            return True
        except User.DoesNotExist:
            self.set_status(401)
            self.write("Invalid API key")
            self.finish()
            return False

    def get(self, widget_id):
        self.check_api_key()
        logger.debug(
            f"Received GET from {self.current_user}: {self.request.body}")
        try:
            widget = Widget.get_by_id(widget_id)
            dict = widget_to_dict(widget)
            self.write(dict)
            logger.info(f"Widget #{dict['id']} returned to requestor.")
        except Widget.DoesNotExist:
            self.set_status(404)
            self.write("Widget not found")
            logger.error(f"Requested widget #{widget_id} not found.")

    def delete(self, widget_id):
        self.check_api_key()
        logger.debug(
            f"Received DELETE from {self.current_user}: {self.request.body}")
        try:
            widget = Widget.get_by_id(widget_id)
            widget.delete_instance()
            self.write("Widget deleted successfully")
            logger.info(f"Widget #{widget_id} deleted.")
        except Widget.DoesNotExist:
            self.set_status(404)
            self.write("Widget not found")
            logger.error(
                f"Requested widget #{widget_id} not found for deletion.")

    def put(self, widget_id):
        self.check_api_key()
        logger.debug(
            f"Received PUT from {self.current_user}: {self.request.body}")
        try:
            widget = Widget.get_by_id(widget_id)
            widget_data = json.loads(self.request.body)
            widget.name = widget_data('name')
            widget.parts = widget_data('parts')
            widget.last_user = self.current_user
            widget.updated_data = datetime.now()
            widget.save()
            self.write(widget_to_dict(widget))
            logger.info(f"Widget #{widget_id} updated.")
        except Widget.DoesNotExist:
            self.set_status(404)
            self.write("Widget not found")
            logger.error(
                f"Requested widget #{widget_id} for update not found.")


class WidgetListHandler(tornado.web.RequestHandler):
    def check_api_key(self):
        api_key = self.request.headers.get('X-API-Key')
        try:
            api_user = User.get(User.api_key == api_key)
            self.current_user = str(api_user.name)
            return True
        except User.DoesNotExist:
            self.set_status(401)
            self.write("Invalid API key")
            self.finish()
            return False

    def get(self):
        if not self.check_api_key():
            return
        logger.info(f"Received GET for all widgets from {self.current_user}")
        widgets = Widget.select()
        widget_list = [widget_to_dict(widget) for widget in widgets]
        self.write(json.dumps(widget_list))
        logger.info("GET for all widgets processed.")

    def post(self):
        if not self.check_api_key():
            return
        logger.debug(
            f"Received POST from {self.current_user}: {self.request.body}")
        status, response, widget_data = validate_widget_data(self.request.body)
        if status == http.HTTPStatus.OK:
            status = 201
            widget = Widget(
                name=widget_data['name'],
                parts=widget_data['parts'],
                last_user=self.current_user,
                created_date=datetime.now(),
                updated_date=datetime.now()
            )
            widget.save()
            dict = widget_to_dict(widget)
            response = dict
            logger.info(f"Created widget #{dict['id']}")
            logger.info(f"POST processed: {status} {response}")
        else:
            logger.error(f"Error processing POST: {status} {response}")

        self.set_status(status)
        self.write(response)
