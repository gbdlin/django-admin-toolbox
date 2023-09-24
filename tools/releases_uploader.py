import argparse
import copy
import enum
import os
import requests
import requests.auth
import re

# import requests
# import logging
#
# import http.client as http_client
# http_client.HTTPConnection.debuglevel = 1
#
# # You must initialize logging, otherwise you'll not see debug output.
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True


class FileFlag(enum.IntFlag):
    UPLOAD = enum.auto()
    UPDATE = enum.auto()
    DELETE = enum.auto()


class PackageFile:
    valid_package_extensions = {
        '.tar.gz': {
            'short_type': 'sdist',
            'full_type': 'sdist',
            'label': 'Python package (sdist)',
            'mime_type': 'application/tar+gzip',
        },
        '.whl': {
            'short_type': 'wheel',
            'full_type': 'bdist-wheel',
            'label': 'Python package (wheel)',
            'mime_type': 'application/octet-stream',
        },
    }
    type_data = {}

    def __init__(self, dir_entry):
        self._dir_entry = dir_entry

        name, ext = os.path.splitext(self.name)
        if ext == '.gz':
            name, ext = os.path.splitext(name)
            ext += '.gz'

        if ext not in self.valid_package_extensions:
            raise Exception()

        self.type_data = self.valid_package_extensions[ext]

        self.package_file_name = name
        self.package_ext = ext
        name_parse = re.match(
            r'^(?P<package>[a-zA-Z0-9_-]+)-(?P<version>(?:\d+!)?\d+(?:\.\d+)*(?:(?:a|b|rc)\d+)?(?:\.post\d+)?(?:\.dev\d+)?)(?:-(?P<arch>[a-zA-Z0-9_.-]+))?$',
            self.package_file_name
        )
        if name_parse is None:
            raise Exception()

        self.package, self.version, self.arch = name_parse.groups()

    def __getattr__(self, item):
        if item in self.type_data:
            return self.type_data[item]
        if hasattr(self._dir_entry, item):
            return getattr(self._dir_entry, item)

    @property
    def type(self):
        return

    def get_gitlab_url(self, tag):
        return (
            f'https://gitlab.com/gbdlin/django-admin-toolbox/-/jobs/artifacts/{tag}/raw/dist/{self.name}'
            f'?job=build:{self.short_type}'
        )


class PypiFile:
    label = 'Package on PyPI'

    def __init__(self, version):
        self.version = version

    def get_gitlab_url(self, tag):
        return f'https://pypi.org/project/django-admin-toolbox/{self.version}/'


class UploaderMetaclass(type):
    def __new__(mcs, name, bases, class_dict):
        cls = super().__new__(mcs, name, bases, class_dict)
        if not len(bases):
            mcs._base = cls
            mcs._base.registered_uploaders = {}
        else:
            registered_name = name
            if name.endswith(mcs._base.__name__):
                registered_name = registered_name[:-len(mcs._base.__name__)]
            registered_name = registered_name.lower()
            mcs._base.registered_uploaders[registered_name] = cls
        return cls


class Uploader(metaclass=UploaderMetaclass):
    RELEASE_GET_URL = None
    RELEASE_CREATE_URL = None
    ARTIFACT_UPLOAD_URL = None
    ARTIFACT_UPDATE_URL = None
    ARTIFACT_UPDATE_METHOD = 'put'

    needs_upload_after_create = False

    _auth_data = None
    _FINAL_VERSION_CHECK = re.compile(
        r'''
            ^
            (?:\d+!)?             # Epoch
            \d+                   # major version
            (?:\.\d+)*            # minor and further versions
            # (?:(?:a|b|rc)\d+)?  # NO pre-release
            (?:\.post\d+)?        # post-release
            # (?:\.dev\d+)?       # NO dev releases
            $
        ''',
        flags=re.VERBOSE,
    )

    @classmethod
    def get_uploader(cls, service, *args, **kwargs):
        return cls.registered_uploaders[service](*args, **kwargs)

    @staticmethod
    def get_files(tag):
        version = tag[1:] if tag.startswith('v') else tag
        for file in os.scandir('dist'):
            try:
                file = PackageFile(file)
            except Exception as e:
                print(e)
                continue
            if file.version == version:
                yield file

    @property
    def auth_data(self):
        if self._auth_data is not None:
            return self._auth_data

        raise NotImplementedError('auth_data must be implemented')

    def is_prerelease(self, version):
        return self._FINAL_VERSION_CHECK.match(version) is None

    def request(self, method, url, *args, data=None, **kwargs):
        method = getattr(requests, method)
        if isinstance(data, (str, bytes)):  # passing data literally
            response = method(
                url,
                *args,
                data=data,
                auth=self.auth_data,
                **kwargs,
            )
        elif isinstance(data, PackageFile):
            kwargs.setdefault('headers', {}).update({
                'Content-Length': f'{data.stat().st_size}',
                'Content-Type': data.mime_type
            })
            with open(data.path, 'rb') as fd:
                response = method(
                    url,
                    *args,
                    data=fd.read(),
                    auth=self.auth_data,
                    **kwargs,
                )
        elif data is not None:  # defaults to JSON
            response = method(
                url,
                *args,
                json=data,
                auth=self.auth_data,
                **kwargs,
            )
        else:  # no data
            response = method(
                url,
                *args,
                auth=self.auth_data,
                **kwargs,
            )
        response.raise_for_status()
        return response

    def get(self, *args, **kwargs):
        return self.request('get', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request('post', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request('put', *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.request('patch', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request('delete', *args, **kwargs)

    def get_or_create_release(self, *, tag, version, name, description, files):
        """
        :param tag:
        :param version:
        :param name:
        :param description:
        :param files:
        :return: 2-tuple with fetched or created release data and True/False if it was created or not
        """
        try:
            resp = requests.get(
                self.RELEASE_GET_URL.format(version=version, tag=tag),
                auth=self.auth_data,
            )
            resp.raise_for_status()
        except requests.HTTPError as e:
            if str(e).startswith('404 ') or str(e).startswith('403 '):
                # release probably doesn't exist, creating new one
                try:
                    resp = self.post(
                        self.RELEASE_CREATE_URL.format(tag, version),
                        data=self.get_release_create_request(
                            tag=tag, version=version, name=name, description=description, files=files)
                    )

                except requests.HTTPError:
                    raise
                else:
                    return resp.json(), True
            raise
        else:
            return resp.json(), False

    def upload_release(self, *, tag, name=None, description=None, files):
        version = tag[1:] if tag.startswith('v') else tag
        name = name or tag  # defaults to tag name

        release, created = self.get_or_create_release(
            tag=tag, version=version, name=name, description=description, files=files)
        release = self.parse_release(release)

        if created and self.needs_upload_after_create:
            self.upload_artifacts(*files, release=release)
        elif not created:
            upload_files, update_files, delete_files = self.diff_files(*files, release=release, version=version)
            self.delete_artifacts(*delete_files, release=release)
            self.upload_artifacts(*upload_files, release=release)
            self.update_artifacts(*update_files, release=release)
            return

    def diff_files(self, *files, **kwargs):
        upload_files = []
        update_files = []
        delete_files = []
        for file in files:
            result = self.diff_file(file, **kwargs)
            if result & FileFlag.UPLOAD:
                upload_files.append(file)
            if result & FileFlag.UPDATE:
                update_files.append(file)
            if result & FileFlag.DELETE:
                delete_files.append(file)

        return upload_files, update_files, delete_files

    def upload_artifacts(self, *files, **kwargs):
        for file in files:
            self.upload_artifact(file, **kwargs)

    def update_artifacts(self, *files, **kwargs):
        for file in files:
            self.update_artifact(file, **kwargs)

    def delete_artifacts(self, *files, **kwargs):
        for file in files:
            self.delete_artifact(file, **kwargs)

    def upload_artifact(self, file, *, release):
        self.post(
            self.ARTIFACT_UPLOAD_URL.format(file=file, release=release),
            data=self.get_release_artifact_upload_request(file=file, release=release),
        )

    def update_artifact(self, file, *, release):
        getattr(self, self.ARTIFACT_UPDATE_METHOD)(
            self.ARTIFACT_UPDATE_URL.format(file=file, release=release),
            data=self.get_release_artifact_update_request(file=file, release=release),
        )

    def delete_artifact(self, file, *, release):
        pass

    def parse_release(self, release):
        return release

    def get_release_create_request(self, *, tag, version, name, description, files):
        raise NotImplementedError('get_release_create_request must be implemented')

    def get_release_artifact_upload_request(self, *, file, release):
        raise NotImplementedError('get_release_artifact_upload_request must be implemented')

    def get_release_artifact_update_request(self, *, file, release):
        raise NotImplementedError('get_release_artifact_update_request must be implemented')

    def diff_file(self, file, *, release, version=None):
        raise NotImplementedError('diff_file must be implemented')


class GithubUploader(Uploader):
    RELEASE_GET_URL = 'https://api.github.com/repos/gbdlin/django-admin-toolbox/releases/tags/v{version}'
    RELEASE_CREATE_URL = 'https://api.github.com/repos/gbdlin/django-admin-toolbox/releases'
    ARTIFACT_UPLOAD_URL = '{release[upload_url]}?name={file.name}&label={file.label}'
    ARTIFACT_UPDATE_URL = '{file.url}'
    ARTIFACT_UPDATE_METHOD = 'patch'
    needs_upload_after_create = True

    def __init__(self, user, key, force_reupload=False):
        self._auth_data = requests.auth.HTTPBasicAuth(user, key)
        self.force_reupload = force_reupload

    def parse_release(self, release):
        release = copy.deepcopy(release)
        if release['upload_url'].endswith('{?name,label}'):
            release['upload_url'] = release['upload_url'][:-13]
        return release

    def get_release_create_request(self, *, tag, version, name, description, files):
        return {
            'tag_name': tag,
            'name': name,
            'prerelease': self.is_prerelease(version),
        }

    def get_release_artifact_upload_request(self, *, file, release):
        return file

    def get_release_artifact_update_request(self, *, file, release):
        return {
            'name': file.name,
            'label': file.label,
        }

    def diff_files(self, *files, **kwargs):
        kwargs['assets'] = {asset['name']: asset for asset in kwargs['release']['assets']}
        return super().diff_files(*files, **kwargs)

    def diff_file(self, file, *, release, assets=None, version=None):
        assets = assets or {}
        flags = FileFlag(0)

        if file.name not in assets:
            flags |= FileFlag.UPLOAD
        else:
            asset = assets[file.name]
            file.url = asset['url']
            if asset['label'] != file.label:
                flags |= FileFlag.UPDATE
        return flags


class PersonalAccessTokenAuth(requests.auth.AuthBase):

    def __init__(self, token):
        self.token = token

    def __eq__(self, other):
        return self.token == getattr(other, 'token', None)

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        r.headers['Private-Token'] = self.token
        return r


class GitlabUploader(Uploader):
    RELEASE_GET_URL = 'https://gitlab.com/api/v4/projects/10980095/releases/{tag}'
    RELEASE_CREATE_URL = 'https://gitlab.com/api/v4/projects/10980095/releases'
    ARTIFACT_UPLOAD_URL = 'https://gitlab.com/api/v4/projects/10980095/releases/{release[tag_name]}/assets/links'
    ARTIFACT_UPDATE_URL = 'https://gitlab.com/api/v4/projects/10980095/releases/{release[tag_name]}/assets/links/{file.asset_id}'
    needs_upload_after_create = False

    def __init__(self, token=None, force_reupload=False):
        if token is not None:
            self._auth_data = PersonalAccessTokenAuth(token)

        self.force_reupload = force_reupload

    def get_release_create_request(self, *, tag, version, name, description, files):
        files.append(PypiFile(version))
        return {
            'tag_name': tag,
            'name': name,
            'description': version,
            'assets': {
                'links': [
                    {
                        'name': file.label,
                        'url': file.get_gitlab_url(tag),
                    } for file in files
                ]
            }
        }

    def get_release_artifact_upload_request(self, *, file, release):
        return {
            'name': file.label,
            'url': file.get_gitlab_url(release['tag_name'])
        }

    def get_release_artifact_update_request(self, *, file, release):
        return {
            'name': file.label,
            'url': file.get_gitlab_url(release['tag_name'])
        }

    def diff_files(self, *files, **kwargs):
        files = list(files)
        files.append(PypiFile(kwargs['version']))
        kwargs['assets'] = {asset['url']: asset for asset in kwargs['release']['assets']['links']}
        return super().diff_files(*files, **kwargs)

    def diff_file(self, file, *, release, assets=None, version=None):
        assets = assets or {}
        flags = FileFlag(0)
        url = file.get_gitlab_url(release['tag_name'])

        if url not in assets:
            flags |= FileFlag.UPLOAD
        else:
            asset = assets[url]
            file.asset_id = asset['id']
            if asset['name'] != file.label:
                flags |= FileFlag.UPDATE
        return flags


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('service', choices=Uploader.registered_uploaders.keys())
    parser.add_argument('tag')
    args = parser.parse_args()

    creds = {
        'github': {
            'user': os.environ.get('GITHUB_USER'),
            'key': os.environ.get('GITHUB_USER_KEY'),
        },
        'gitlab': {
            'token': os.environ.get('GITLAB_PRIVATE_KEY', os.environ.get('CI_JOB_TOKEN')),
        }
    }

    uploader = Uploader.get_uploader(args.service, **creds[args.service])
    files = list(Uploader.get_files(args.tag))

    uploader.upload_release(tag=args.tag, files=files)
