#!/usr/bin/env python

import argparse
import datetime
import logging
import os

import citizenpy


def main(log_level, show_incidents, show_leaders, show_geo, show_radio, city, limit, username, password):
    logging.basicConfig(level=log_level, format='%(asctime)s [%(levelname)s](%(processName)s:%(funcName)s):%(message)s')

    if username:
        if username == '-':
            username = input('Username: ')
        if password == '-':
            password = input('Password: ')
    else:
        username = None
        password = None

    client = citizenpy.Client()
    session = client.guest_session()

    if username:
        auth_session = session.authenticate(username=username, password=password)
        user_info = auth_session.get_user()
        print(user_info)

    # NYC
    city = city.lower()
    if city == 'nyc':
        max_lat = 40.78176680680204
        min_lat = 40.64371223133252
        max_long = -73.95627683137207
        min_long = -74.05566876862792
        center_lat = 40.7299223
        center_long = -74.0004182
    # SF
    elif city == 'sf':
        max_lat = 37.939186003638675
        min_lat = 37.638021519017606
        max_long = -122.1457424224638
        min_long = -122.61781120908489
        center_lat = 37.7756343
        center_long = -122.4269649
    elif city == 'la':
        max_lat = 34.173994148348115
        min_lat = 33.98732610713007
        max_long = -117.95190643682477
        min_long = -118.59301604243592
        center_lat = 0.5 * (min_lat + max_lat)
        center_long = 0.5 * (min_long + max_long)
    else:
        raise ValueError('Invalid city {}. The valid values are: la, sf, nyc'.format(city))

    if show_incidents:
        logging.info('Retrieving incidents')
        incident_ids = session.get_nearby_incident_ids(
            max_lat=max_lat,
            min_lat=min_lat,
            max_long=max_long,
            min_long=min_long,
            limit=limit)
        print ('{} incidents found'.format(len(incident_ids)))

        incident_ids2 = session.query(
            since=datetime.datetime.now() - datetime.timedelta(days=1),
            max_lat=max_lat,
            min_lat=min_lat,
            max_long=max_long,
            min_long=min_long
        )
        print('{} incidents found'.format(len(incident_ids2)))

        incidents = session.get_incidents_v1(incident_ids2)
        for incident in incidents:
            print(f'{incident.createdAt} {incident.title} [{incident.address}]')

    if show_leaders:
        logging.info('Retrieving leaders')
        leaders = session.get_leaders()
        for leader in leaders:
            print ('{username:24} {incidentCount}/{flagCount}'.format(**leader))

    if show_geo:
        logging.info('Retrieving Geo info')
        print ('{}:{}'.format(center_lat, center_long))
        service = session.get_service_area_code(center_lat, center_long)
        print ('{name} ({code})'.format(**service))
        for neighborhood in session.get_neighborhoods(center_lat, center_long):
            print('{name} in {city},{state}'.format(**neighborhood))
        radius = session.get_suggested_radius(center_lat, center_long)
        print ('Radius: {radius} ({reason})'.format(**radius))
        for precinct in session.get_precincts(center_lat, center_long):
            print ('Precinct: {name}'.format(**precinct))

    if show_radio:
        # Store channel data by channel id, so it can be matched with clips
        channels = {}
        for channel in session.get_channels():
            channels[channel['id']] = channel
        channels_with_clips = [channel['id'] for channel in channels.values() if channel['clipCount'] > 0]
        clips = session.get_clips(channels_with_clips)
        for clip in clips:
            clip_channel_id = clip['channel']
            clip_channel = channels.setdefault(clip_channel_id, {})
            clip_channel.setdefault('clips', []).append(clip)
        for channel_id, channel in channels.items():
            print('{id} {name} {department} in {subArea},{serviceArea}'.format(**channel))
            for clip in channel.get('clips', []):
                print ('Freq: {frequency} {wav_url} ({duration_ms}ms)'.format(**clip))
            print ('')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Police Scanner')
    parser.add_argument('--log-level', type=int, nargs='?', dest='log_level',
                        help='Sets logging level', default=logging.INFO, required=False)
    parser.add_argument('--verbose', '-v', action='store_const', const=logging.DEBUG, dest='log_level',
                        help='Show verbose output')
    parser.add_argument('--quiet', '-q', action='store_const', const=logging.WARNING, dest='log_level',
                        help='Suppress output')
    parser.add_argument('--username', action='store', nargs='?', default=os.environ.get('GUARDIAN_USERNAME'),
                        help='Login username (your mobile phone #)')
    parser.add_argument('--password', action='store', nargs='?', default=os.environ.get('GUARDIAN_PASSWORD'),
                        help='Login password')
    parser.add_argument('--show-incidents', action='store_true', default=False, help='Show incidents')
    parser.add_argument('--show-leaders', action='store_true', default=False, help='Show leaderboard')
    parser.add_argument('--show-geo', action='store_true', default=False, help='Show geographic info')
    parser.add_argument('--show-radio', action='store_true', default=False, help='Show radio')
    parser.add_argument('--city', default='nyc', const='nyc', nargs='?', choices=['nyc', 'sf', 'la'], help='City to get information about')
    parser.add_argument('-l', '--limit', action='store', nargs='?', default=10, type=int, help='Number of items to fetch')
    main(**parser.parse_args().__dict__)
