#!/usr/bin/env hython

"""Construct USD Files Containing SG references."""

import logging

from rbl_pipe_core.util import get_project

from rbl_pipe_sg import load

from rbl_pipe_usd.build import constructusd
from rbl_pipe_usd.resolve import uribuilder


logger = logging.getLogger(__name__)


class SGConstructUSD(constructusd.ConstructUSD):
    """Class to handle the construction of USD files based on SG data."""

    def __init__(
        self,
        sg_script,
        sg_key,
        project=None,
    ):
        """
        Initialise the SG USD builder.

        Args:
            sg_script(str): The SG script to use.
            sg_key(str): The SG key to use.
            project(str): The SG project to initialise with.
        """
        self.project = project or get_project()
        self.sg_load = load.ShotgunLoad(sg_script, sg_key)
        self.uri_builder = uribuilder.UriBuilder(sg_script, sg_key)
        super(SGConstructUSD, self).__init__()

    def reference_name(self, asset_id, instance_id=None, include_parent_transform=True):
        """
        Generate the name to use for the reference.

        Args:
            asset_id(int): The asset ID to use.
            instance_id(str): A padded instance ID string to use.
            include_parent_transform(bool): Should we create the reference including a
                parent transform.

        Returns:
            reference_name(str): The name to use for the reference.
        """
        asset_name = self.sg_load.asset_name_from_id(asset_id)
        if instance_id:
            reference_name = "/{asset_name}_{instance_id}".format(
                asset_name=asset_name,
                instance_id=instance_id,
            )
        else:
            reference_name = "/{asset_name}".format(
                asset_name=asset_name,
            )

        if include_parent_transform:
            reference_name = "{reference}/{asset_name}".format(
                reference=reference_name,
                asset_name=asset_name,
            )

        return reference_name

    def reference_primitive_path(self, asset_id):
        """
        Generate the primitive path to reference. For this case this is the asset name.

        Args:
            asset_id(int): The asset ID to use.

        Returns:
            (str): The primitive path to reference from.
        """
        return "/{asset_name}".format(
            asset_name=self.sg_load.asset_name_from_id(asset_id),
        )

    def get_variant_task_id(self, variant_name, step, asset_id=None, shot_id=None):
        """
        Get the task ID for the given asset_id, variant_name and step.

        Args:
            variant_name(str): The variant name to lookup the task for.
            step(str): The step to lookup the task for.
            asset_id(int): The asset_id to lookup the task for.
            shot_id(int): The shot_id to lookup the task for.

        Returns:
            (int): The task ID for the generated inputs.
        """
        task_name = self.get_variant_task_name(variant_name, step)

        return self.sg_load.task_id_from_name(
            task_name, asset_id=asset_id, shot_id=shot_id
        )

    def get_variant_task_name(self, variant_name, step):
        """
        Get the task name for the given variant and step.

        Args:
            variant_name(str): The variant to generate the task name for.
            step(str): The step to generate the task name for.

        Returns:
            (str): The generated task name.
        """
        return "{variant}_{step}".format(
            variant=variant_name,
            step=step,
        )

    def add_reference(
        self,
        asset_id,
        step,
        variant_name,
        template,
        instance_id=None,
        version_rule="latest",
        include_parent_transform=True,
        over=False,
    ):
        """
        Add a reference to be written to the USD scene.

        Args:
            asset_id(int): The asset ID to use for the reference.
            variant_name(str): The variant name to use for the reference.
            step(str): The step to use for the reference.
            instance_id(str): The padded instance ID string to use for the reference.
            version_rule(str): The version rule to use when creating the URI.
            template(str): The SG template to use when creating the URI.
            include_parent_transform(bool): Should we create the reference including a
                parent transform.
            over(bool): If True ``over`` is going to be used instead of ``def``
                (default).

        Raises:
            RuntimeError: The task_id, name, or primitive path required to create a
                reference couldn't be generated.
        """
        asset_name = self.sg_load.asset_name_from_id(asset_id)
        logger.debug(
            "Adding reference {name} ({id}), {variant}, {step}".format(
                name=asset_name,
                id=asset_id,
                variant=variant_name,
                step=step,
            )
        )

        # Generate the name (ie. primitive path) to use for the reference.
        name = self.reference_name(
            asset_id,
            instance_id=instance_id,
            include_parent_transform=include_parent_transform,
        )
        if not name:
            raise RuntimeError("A name couldn't be generated.")

        # Get the task ID and generate the URI.
        task_id = self.get_variant_task_id(variant_name, step, asset_id=asset_id)
        if not task_id:
            raise RuntimeError(
                (
                    "Error creating reference: No task_id could be found for asset: "
                    "{asset_name} ({asset_id}), variant_name: {variant_name}, step: "
                    "{step}"
                ).format(
                    asset_name=asset_name,
                    asset_id=asset_id,
                    variant_name=variant_name,
                    step=step,
                )
            )

        # Get the primitive path which we want to reference from.
        primitive_path = self.reference_primitive_path(asset_id)

        if not primitive_path:
            raise RuntimeError("The reference primitive path couldn't be generated.")

        self.reference_by_taskid(
            task_id,
            template,
            name,
            primitive_path,
            version_rule=version_rule,
            over=over,
        )

    def add_sublayer(
        self,
        shot_id,
        step,
        variant_name,
        template,
        version_rule="latest",
    ):
        """
        Add a sublayer to be referenced in the USD scene.

        Args:
            shot_id(int): The asset ID to use for the reference.
            step(str): The step to use for the reference.
            variant_name(str): The variant name to use for the reference.
            template(str): The SG template to use when creating the URI.
            version_rule(str): The version rule to use when creating the URI.

        Raises:
            RuntimeError: A task ID couldn't be found for the given shot ID.
        """
        shot_name = self.sg_load.shot_name_from_id(shot_id)
        logger.debug(
            "Adding sublayer {name} ({id}), {variant}, {step}".format(
                name=shot_name,
                id=shot_id,
                variant=variant_name,
                step=step,
            )
        )

        # Get the task ID and generate the URI.
        task_id = self.get_variant_task_id(variant_name, step, shot_id=shot_id)
        if not task_id:
            raise RuntimeError(
                (
                    "Error creating sublayer: No task_id could be found for shot: "
                    "{shot_name} ({shot_id}), variant_name: {variant_name}, step: "
                    "{step}"
                ).format(
                    shot_name=shot_name,
                    shot_id=shot_id,
                    variant_name=variant_name,
                    step=step,
                )
            )

        self.sublayer_by_taskid(task_id, template, version_rule)

    def reference_by_taskid(
        self,
        task_id,
        template,
        name,
        primitive_path,
        version_rule="latest",
        variant_name=None,
        variant_set=None,
        over=False,
    ):
        """
        Add a reference based on task ID, template, name and primitive path.

        Args:
            task_id(int): The task ID to reference.
            template(str): The template to use when creating the URI.
            name(str): The name to create the reference at within the scene graph.
            primitive_path(str): The path to reference from.
            version_rule(str): The version rule to use when creating the URI.
            variant_name(str): The USD variant name to use for the reference.
            variant_set(str): The USD variant set to create the reference within.
            over(bool): If True ``over`` is going to be used instead of ``def``
                (default).

        Raises:
            RuntimeError: A URI couldn't be generated.
        """
        uri = self.uri_builder.build_task_uri(
            self.project.upper(),
            template,
            task_id,
            version=version_rule,
        )
        if not uri:
            raise RuntimeError("A URI couldn't be generated.")

        # Add to our list of references
        self.append_reference(
            name,
            uri,
            primitive_path,
            variant_name=variant_name,
            variant_set=variant_set,
            over=over,
        )

    def sublayer_by_taskid(self, task_id, template, version_rule="latest"):
        """
        Add a sublayer based on task_id and template.

        Args:
            task_id(int): The task ID to sublayer.
            template(str): The template to use when creating the URI.
            version_rule(str): The version rule to use when creating the URI.

        Raises:
            RuntimeError: A URI couldn't be generated.
        """
        uri = self.uri_builder.build_task_uri(
            self.project.upper(),
            template,
            task_id,
            version=version_rule,
        )
        if not uri:
            raise RuntimeError("A URI couldn't be generated.")

        # Add to our list of sublayers
        self.append_sublayer(uri)
