#!/usr/bin/env python3
"""
Feature Flag Deployment Script
SOW Day 3 Requirement: Deploy feature flag configurations to AWS SSM Parameter Store

This script reads the feature-flag-config.json file and creates the necessary
SSM parameters for the feature flag system.
"""

import json
import boto3
import sys
from botocore.exceptions import ClientError
from typing import Dict, Any


def load_feature_flag_config(config_file: str = 'feature-flag-config.json') -> Dict[str, Any]:
    """Load feature flag configuration from JSON file."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file {config_file} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {config_file}: {e}")
        sys.exit(1)


def create_ssm_parameter(ssm_client, parameter_name: str, parameter_value: str,
                        description: str, overwrite: bool = True) -> bool:
    """Create or update an SSM parameter."""
    try:
        ssm_client.put_parameter(
            Name=parameter_name,
            Value=parameter_value,
            Type='String',
            Description=description,
            Overwrite=overwrite,
            Tags=[
                {'Key': 'Project', 'Value': 'JubileeKYC'},
                {'Key': 'Component', 'Value': 'FeatureFlags'},
                {'Key': 'Environment', 'Value': 'staging'},
                {'Key': 'ManagedBy', 'Value': 'feature-flag-deployment'},
                {'Key': 'SOWPhase', 'Value': 'Day3'}
            ]
        )
        print(f"Created/Updated parameter: {parameter_name}")
        return True
    except ClientError as e:
        print(f"Error creating parameter {parameter_name}: {e}")
        return False


def deploy_feature_flags(config: Dict[str, Any], parameter_prefix: str = '/jubilee/kyc/feature-flags') -> None:
    """Deploy feature flags to SSM Parameter Store."""
    ssm_client = boto3.client('ssm')

    feature_flags = config.get('feature_flags', {})
    success_count = 0
    total_count = len(feature_flags)

    print(f"Deploying {total_count} feature flags to SSM Parameter Store...")
    print(f"Parameter prefix: {parameter_prefix}")
    print()

    for flag_name, flag_config in feature_flags.items():
        parameter_name = f"{parameter_prefix}/{flag_name}"
        parameter_value = json.dumps(flag_config, indent=2)
        description = flag_config.get('description', f'Feature flag for {flag_name}')

        if create_ssm_parameter(ssm_client, parameter_name, parameter_value, description):
            success_count += 1

    print()
    print(f"Deployment Summary:")
    print(f"   Successfully deployed: {success_count}/{total_count}")
    print(f"   Failed: {total_count - success_count}/{total_count}")

    if success_count == total_count:
        print("All feature flags deployed successfully!")
    else:
        print("Some feature flags failed to deploy. Check the errors above.")


def deploy_emergency_config(config: Dict[str, Any], parameter_prefix: str = '/jubilee/kyc/feature-flags') -> None:
    """Deploy emergency configuration parameters."""
    ssm_client = boto3.client('ssm')

    emergency_config = config.get('emergency_flags', {})
    monitoring_config = config.get('monitoring', {})

    # Deploy emergency configuration
    emergency_param = f"{parameter_prefix}/emergency-config"
    emergency_value = json.dumps(emergency_config, indent=2)
    create_ssm_parameter(
        ssm_client,
        emergency_param,
        emergency_value,
        "Emergency feature flag configuration for kill switches and degradation handling"
    )

    # Deploy monitoring configuration
    monitoring_param = f"{parameter_prefix}/monitoring-config"
    monitoring_value = json.dumps(monitoring_config, indent=2)
    create_ssm_parameter(
        ssm_client,
        monitoring_param,
        monitoring_value,
        "Monitoring configuration for feature flag system"
    )


def verify_deployment(parameter_prefix: str = '/jubilee/kyc/feature-flags') -> None:
    """Verify that feature flags were deployed correctly."""
    ssm_client = boto3.client('ssm')

    try:
        # Get all parameters with our prefix
        paginator = ssm_client.get_paginator('get_parameters_by_path')
        page_iterator = paginator.paginate(
            Path=parameter_prefix,
            Recursive=True,
            ParameterFilters=[
                {
                    'Key': 'Type',
                    'Values': ['String']
                }
            ]
        )

        parameters = []
        for page in page_iterator:
            parameters.extend(page.get('Parameters', []))

        print(f"\nVerification Results:")
        print(f"   Found {len(parameters)} parameters under {parameter_prefix}")

        for param in parameters:
            param_name = param['Name'].replace(parameter_prefix + '/', '')
            print(f"   {param_name}")

            # Validate JSON structure
            try:
                json.loads(param['Value'])
            except json.JSONDecodeError:
                print(f"   {param_name} - Invalid JSON structure")

        print("\nVerification complete!")

    except ClientError as e:
        print(f"Error during verification: {e}")


def rollback_deployment(parameter_prefix: str = '/jubilee/kyc/feature-flags') -> None:
    """Rollback feature flag deployment by deleting all parameters."""
    ssm_client = boto3.client('ssm')

    print(f"Rolling back feature flag deployment...")
    print(f"This will DELETE ALL parameters under {parameter_prefix}")

    confirm = input("Are you sure you want to proceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Rollback cancelled")
        return

    try:
        # Get all parameters to delete
        paginator = ssm_client.get_paginator('get_parameters_by_path')
        page_iterator = paginator.paginate(
            Path=parameter_prefix,
            Recursive=True
        )

        parameters_to_delete = []
        for page in page_iterator:
            for param in page.get('Parameters', []):
                parameters_to_delete.append(param['Name'])

        # Delete parameters in batches (SSM allows max 10 at a time)
        batch_size = 10
        for i in range(0, len(parameters_to_delete), batch_size):
            batch = parameters_to_delete[i:i + batch_size]
            ssm_client.delete_parameters(Names=batch)
            print(f"Deleted batch: {[p.split('/')[-1] for p in batch]}")

        print(f"Rollback complete! Deleted {len(parameters_to_delete)} parameters")

    except ClientError as e:
        print(f"Error during rollback: {e}")


def main():
    """Main deployment function."""
    import argparse

    parser = argparse.ArgumentParser(description='Deploy KYC feature flags to AWS SSM Parameter Store')
    parser.add_argument('--config', default='feature-flag-config.json',
                       help='Path to feature flag configuration file')
    parser.add_argument('--prefix', default='/jubilee/kyc/feature-flags',
                       help='SSM parameter prefix')
    parser.add_argument('--verify', action='store_true',
                       help='Verify deployment after completion')
    parser.add_argument('--rollback', action='store_true',
                       help='Rollback deployment (delete all parameters)')

    args = parser.parse_args()

    if args.rollback:
        rollback_deployment(args.prefix)
        return

    # Load and deploy configuration
    config = load_feature_flag_config(args.config)

    # Deploy feature flags
    deploy_feature_flags(config, args.prefix)

    # Deploy emergency and monitoring configuration
    deploy_emergency_config(config, args.prefix)

    # Verify deployment if requested
    if args.verify:
        verify_deployment(args.prefix)

    print("\nFeature Flag Deployment Complete!")
    print("\nNext Steps:")
    print("   1. Test feature flag functionality with the new endpoint")
    print("   2. Monitor CloudWatch logs for feature flag evaluations")
    print("   3. Gradually increase rollout percentages as confidence grows")
    print("   4. Use emergency configuration if rollback is needed")


if __name__ == '__main__':
    main()