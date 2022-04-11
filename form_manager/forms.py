"""Endpoints related to forms."""
import flask

from form_manager import utils

blueprint = flask.Blueprint("forms", __name__)  # pylint: disable=invalid-name


@blueprint.route("", methods=["GET"])
def list_forms():
    form_info = list(flask.g.db["forms"].find({"owner": flask.session["email"]}, {"_id": 0}))
    flask.current_app.logger.error(form_info)
    return flask.jsonify({"forms": form_info,
                          "url": flask.url_for("forms.list_forms", _external=True)})


@blueprint.route("", methods=["POST"])
def add_form():
    indata = flask.request.json
    if indata.get("identifier"):
        if flask.g.db["forms"].find_one({"identifier": indata["identifier"]}):
            flask.abort(status=400)
    indata["owner"] = flask.session["email"]
    flask.g.db["forms"].insert_one(indata)
    return flask.Response(status=200)


@blueprint.route("/incoming/<form_identifier>", methods=["POST"])
def receive_response(form_identifier:str):
    """
    Save the response for the form to the db.

    Args:
        form_identifier (str): The identifier for the submitted form
    """
    form_info = flask.g.db["forms"].find_one({"identifier": form_identifier})
    if not form_info:
        return flask.abort(status=400)
    form_response = dict(flask.request.form)

    to_add = {
        "response": form_response,
        "timestamp": utils.make_timestamp()
    }
    
    flask.g.db[f"form_{form_identifier}"].insert_one(to_add)

    if form_info.get("target_email"):
        utils.send_email()
    return flask.Response(status=200)


@blueprint.route("/<identifier>/responses", methods=["GET"])
def get_responses(identifier):
    responses = list(flask.g.db[f"form_{identifier}"].find(projection={"_id": 0}))
    return flask.jsonify({
        "responses": responses,
        "url": flask.url_for("forms.get_responses", identifier=identifier, _external=True)
    })
