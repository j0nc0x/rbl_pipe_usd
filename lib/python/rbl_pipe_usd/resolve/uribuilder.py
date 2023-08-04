#!/usr/bin/env python

"""Construct URIs from SG data."""

import logging

from rbl_pipe_sg import load
from rbl_pipe_sg import template

from rbl_pipe_usd.resolve import ar


logger = logging.getLogger(__name__)


class UriBuilder(object):
    """Class to handle building URIs based on SG data."""

    def __init__(self, sg_script, sg_key):
        """
        Initialise the URI builder.

        Args:
            sg_script(str): The SG script to use.
            sg_key(str): The SG key to use.
        """
        self.sg_load = load.ShotgunLoad.get_instance(sg_script, sg_key)
        self.sg_template = template.SGTemplate(sg_script, sg_key)

    def valid_version(self, version):
        """
        Validate the the given version string.

        Args:
            version(str): The version string.

        Returns:
            (bool): Is the version valid?
        """
        if version == "latest" or version.isnumeric():
            return True

        return False

    def build_task_uri(
        self,
        project,
        template_name,
        task_id,
        version="latest",
    ):
        """
        Build a URI for the given task.

        Args:
            project(str): The project to use when constructing the URI.
            template_name(str): The template to use when constructing the URI.
            task_id(int): The task_id to use when generating the fields to use in the
                URI.
            version(str): The version to use when generating the URI.

        Returns:
            (str): The generated URI.

        Raises:
            RuntimeError: The context couldn't be determined from the template.
        """
        if self.sg_template.is_asset_template(template_name):
            asset_id = self.sg_load.asset_id_from_task_id(task_id)
            step_name = self.sg_load.step_from_task(task_id)
            asset_name = self.sg_load.asset_name_from_id(asset_id)
            variant_name = self.sg_load.variant_name_from_task(task_id)

            # Validate the inputs before building the URI
            params = dict(
                project=project,
                template=template_name,
                asset=asset_name,
                step=step_name,
                variant=variant_name,
                version=version,
            )
            if None in params.values() or not self.valid_version(version):
                raise RuntimeError(
                    "Invalid inputs found when building URI. Project: {project}, "
                    "Template: {template}, Task ID: {task} (Asset: {asset}, Step: "
                    "{step}, Variant: {variant}), Version: {version}.".format(
                        task=task_id,
                        **params,
                    )
                )

            return ar.build_uri(
                project,
                template_name,
                Step=step_name,
                Asset=asset_name,
                variant_name=variant_name,
                version=version,
            )
        elif self.sg_template.is_shot_template(template_name):
            shot_id = self.sg_load.shot_id_from_task_id(task_id)
            step_name = self.sg_load.step_from_task(task_id)
            shot_name = self.sg_load.shot_name_from_id(shot_id)
            variant_name = self.sg_load.variant_name_from_task(task_id)

            # Validate the inputs before building the URI
            params = dict(
                project=project,
                template=template_name,
                shot=shot_name,
                step=step_name,
                variant=variant_name,
                version=version,
            )
            if None in params.values() or not self.valid_version(version):
                raise RuntimeError(
                    "Invalid inputs found when building URI. Project: {project}, "
                    "Template: {template}, Task ID: {task} (Shot: {shot}, Step: "
                    "{step}, Variant: {variant}), Version: {version}.".format(
                        task=task_id,
                        **params,
                    )
                )

            return ar.build_uri(
                project,
                template_name,
                Step=step_name,
                Shot=shot_name,
                variant_name=variant_name,
                version=version,
            )
        else:
            raise RuntimeError(
                "Could not determine asset or shot context from template."
            )
