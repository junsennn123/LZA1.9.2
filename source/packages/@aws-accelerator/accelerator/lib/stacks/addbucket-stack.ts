/**
 *  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 *  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
 *  with the License. A copy of the License is located at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES
 *  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions
 *  and limitations under the License.
 */

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { AcceleratorStack, AcceleratorStackProps, NagSuppressionRuleIds } from './accelerator-stack';

import { Bucket, BucketEncryptionType } from '@aws-accelerator/constructs';

export class AddBucketStack extends AcceleratorStack {
  constructor(scope: Construct, id: string, props: AcceleratorStackProps) {
    super(scope, id, props);

    const serverAccessLogsBucketName = this.getServerAccessLogsBucketName();
    const addBucketTest = new Bucket(this, 'add-bucket', {
      s3BucketName: `${this.acceleratorResourceNames.bucketPrefixes.addBucket}-${cdk.Stack.of(this).account}-${
        cdk.Stack.of(this).region
      }`,
      encryptionType: this.isS3CMKEnabled ? BucketEncryptionType.SSE_KMS : BucketEncryptionType.SSE_S3,
      serverAccessLogsBucketName: `${this.acceleratorResourceNames.bucketPrefixes.addBucket}-${
        cdk.Stack.of(this).account
      }-${cdk.Stack.of(this).region}`,
      //autoDeleteObjects: true,
    });

    if (!serverAccessLogsBucketName) {
      // AwsSolutions-S1: The S3 Bucket has server access logs disabled
      this.nagSuppressionInputs.push({
        id: NagSuppressionRuleIds.S1,
        details: [
          {
            path: `/${this.stackName}/add-bucket/Resource/Resource`,
            reason: 'Due to configuration settings, server access logs have been disabled.',
          },
        ],
      });
    }

    //addBucketTest.getS3Bucket().grantRead();

    addBucketTest.getKey();
  }
}
