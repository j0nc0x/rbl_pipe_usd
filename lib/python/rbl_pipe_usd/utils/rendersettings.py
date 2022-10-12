#!/usr/bin/env python

"""USD Utils relating to the rendersettings."""

import logging


logger = logging.getLogger(__name__)


def get_render_products(usd_stage, render_settings_path):
    """
    Get the render products from the given USD stage.

    Args:
        usd_stage(Usd.Stage): The usd stage to look for the render products in.
        render_settings_path(str): The render settings path to look for the products.

    Returns:
        str: The resolved file path.
    """
    render_settings = usd_stage.GetPrimAtPath(render_settings_path)

    if not render_settings:
        logger.warning("No render directories could be found.")
        return []

    # get all products_paths
    product_paths = render_settings.GetProperty("products").GetTargets()

    # See if the render product exist
    if len(product_paths) == 0:
        logger.warning("No render products found.")

    render_products = []

    # get productname
    for product_path in product_paths:
        product = usd_stage.GetPrimAtPath(product_path)

        if not product:
            logger.warning(
                "Render product not found at {path}.".format(
                    path=product_path,
                )
            )
            continue

        render_products.append(product)

    return render_products


def get_product_output_path(product, frame=1):
    """
    Get the render product output path for the given product.

    Args:
        product(Usd.Prim): The render product to get the path for.
        frame(int): The frame number to query the output path for.

    Returns:
        product_output_path(st): The output file path used by the given render
            product.
    """
    product_output_path = product.GetProperty("productName").Get(
        time=frame,
    )

    if not product_output_path:
        return None

    logger.info(
        "Output Image in Render Product found: {path}.".format(
            path=product_output_path,
        )
    )

    return product_output_path


def get_output_paths(usd_stage, render_settings_path, frame=1):
    """
    Get output paths for the specified stet of render settings.

    Args:
        usd_stage(Usd.Stage): The usd stage to look for the output paths in.
        render_settings_path(str): The usd scene graph path to the setting we
            want to look in.
        frame(int): The frame number to query the output paths for.

    Returns:
        output_paths(list): A list of output image paths.
    """
    output_paths = []

    products = get_render_products(
        usd_stage,
        render_settings_path,
    )

    for product in products:
        output_path = get_product_output_path(
            product,
            frame=frame,
        )
        output_paths.append(output_path)

    return output_paths
