# Copyright 2020 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The Python AsyncIO implementation of the GRPC helloworld.Greeter server."""

import logging
import grpc

import alco_pb2
import alco_pb2_grpc

from concurrent import futures
import numpy as np
from PIL import Image
import pickle
import os
from datetime import datetime
import json

_ONE_MEGABYTES = 1024 * 1024


class AlcoServer(alco_pb2_grpc.CaregiverResultServicer):
    def __init__(self):
        super(alco_pb2_grpc.CaregiverResultServicer, self).__init__()

    def push_result(self, request, context):
        try:
            data = {}
            data['delivery_time'] = request.delivery_time
            data['detected_time'] = request.detected_time
            data['detected_value'] = request.detected_value
            # try:
            date = datetime.strptime(data['delivery_time'], '%Y%m%d-%H:%M:%S.%f')
            day_folder = date.strftime('%Y%m%d')
            hour_folder = date.strftime('%Y%m%d%H')
            if request.pushing_mode == '1':
                path_json = os.path.join(os.path.join('/ram/' + day_folder, hour_folder), 'second_log/json')
                path_image = os.path.join(os.path.join('/ram/' + day_folder, hour_folder), 'second_log/frame')
            else:
                path_json = os.path.join(os.path.join('/ram/' + day_folder, hour_folder), 'detected_log/json')
                path_image = os.path.join(os.path.join('/ram/' + day_folder, hour_folder), 'detected_log/frame')
            try:
                os.makedirs(path_json)
                os.makedirs(path_image)
            except:
                pass
            im = Image.fromarray(np.array(pickle.loads(request.image)))
            im.save(os.path.join(path_image, data['delivery_time']+'.jpg'))
            data['image'] = data['delivery_time']+'.jpg'
            with open(os.path.join(path_json, data['delivery_time']+'.json'), 'w') as outfile:
                json.dump(data, outfile)
            return alco_pb2.CaregiverResultPushingResponse(pushing_status=200)
        except:
            return alco_pb2.CaregiverResultPushingResponse(pushing_status=400)

def serve():
    max_worker = 5
    max_len = 100
    channel_opt = [('grpc.max_send_message_length', max_len * _ONE_MEGABYTES), ('grpc.max_receive_message_length', max_len * _ONE_MEGABYTES)]
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_worker), options=channel_opt)
    alco_pb2_grpc.add_CaregiverResultServicer_to_server(AlcoServer(), server)
    listen_addr = '[::]:5000'
    server.add_insecure_port(listen_addr)
    logging.info("Starting server on %s", listen_addr)
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        # Shuts down the server with 0 seconds of grace period. During the
        # grace period, the server won't accept new connections and allow
        # existing RPCs to continue within the grace period.
        server.stop(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve()
