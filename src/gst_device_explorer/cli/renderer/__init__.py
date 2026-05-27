"""Text and JSON rendering for gst-device-explorer CLI."""

from __future__ import annotations

from gst_device_explorer.cli.renderer._utils import (
    print_json_error,
)
from gst_device_explorer.cli.renderer.analysis import (
    print_candidate_ranking,
    print_device_profile,
    print_group_not_found,
    print_group_validation,
    print_pipeline_candidates,
    print_pipeline_diagnostics,
    print_system_report,
)
from gst_device_explorer.cli.renderer.config import (
    print_config_paths,
    print_config_show,
    print_config_validate,
    print_schema_document,
    print_schema_list,
    print_schema_not_found,
)
from gst_device_explorer.cli.renderer.devices import (
    print_composite_group,
    print_composite_groups,
    print_devices,
    print_environment,
    print_grouping_metadata,
    print_support_bundle_written,
    print_suggestions_catalog,
    print_video_capabilities,
)
from gst_device_explorer.cli.renderer.execution import (
    print_capture_completed,
    print_capture_not_started_existing_output,
    print_capture_plan,
    print_execution_plan,
)
from gst_device_explorer.cli.renderer.presets import (
    print_preset,
    print_preset_command_suggestions,
    print_preset_error,
    print_preset_list,
    print_preset_not_found,
)

__all__ = [
    "print_candidate_ranking",
    "print_capture_completed",
    "print_capture_not_started_existing_output",
    "print_capture_plan",
    "print_composite_group",
    "print_composite_groups",
    "print_config_paths",
    "print_config_show",
    "print_config_validate",
    "print_device_profile",
    "print_devices",
    "print_environment",
    "print_execution_plan",
    "print_group_not_found",
    "print_group_validation",
    "print_grouping_metadata",
    "print_json_error",
    "print_pipeline_candidates",
    "print_pipeline_diagnostics",
    "print_preset",
    "print_preset_command_suggestions",
    "print_preset_error",
    "print_preset_list",
    "print_preset_not_found",
    "print_schema_document",
    "print_schema_list",
    "print_schema_not_found",
    "print_support_bundle_written",
    "print_suggestions_catalog",
    "print_system_report",
    "print_video_capabilities",
]
