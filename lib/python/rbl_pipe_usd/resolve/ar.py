#!/usr/bin/env python

"""USD Asset Resolve Related Utils."""

import logging

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from pxr import Ar


logger = logging.getLogger(__name__)


def resolve_path(uri):
    """Resolve the given Asset Reference using the AR.

    Args:
        uri(str): The URI we want to resolve with the AR.

    Returns:
        str: The resolved file path.
    """
    resolver = Ar.GetUnderlyingResolver()
    return resolver.Resolve(uri)


def build_uri(project, template, **kwargs):
    """Build a URI for use with our AR.

    To do this we require the project and template name with the rest of the URI being
    constructed from the kwargs.

    Args:
        project(str): The project to build the URI for.
        template(str): The template to build the URI for.
        **kwargs: Further keyword arguments used to construct the remainder of the URI.

    Returns:
        uri(str): The constructed URI.
    """
    logger.debug("URI input arguments: {inputs}".format(inputs=kwargs))

    if not kwargs:
        logger.warning(
            "At least one keyword argument should be supplied to generate a valid URI."
        )

    query = urlencode(kwargs)

    uri = "tank:/{project}/{template}?{query}".format(
        project=project,
        template=template,
        query=query,
    )
    logger.debug("URI generated: {uri}".format(uri=uri))

    return uri


def is_asset_ref(path):
    """
    Check if a given path is a URI for use with out Asset Resolver.

    Args:
        path(str): A URI string.

    ReturnsL
        (bool): Is the path an asset reference.
    """
    return path.startswith("tank:")
