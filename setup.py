from setuptools import setup
from setuptools import find_packages

with open("README.md") as f:
    long_description = f.read()

setup(
    name="pre_commit_nb",
    version="0.2.2a4",
    description="Set of git pre-commit hooks for Jupyter Notebooks compatible with https://pre-commit.com/ framework",  # NOQA E501
    long_description=long_description,
    long_description_content_type="text/markdown",  # This is important!
    url="http://github.com/karolzak/pre-commit-nb",
    author="Karol Zak",
    author_email="karol.zak@hotmail.com",
    license="MIT",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    packages=find_packages(),
    zip_safe=False,
    install_requires=[],
    entry_points={
        "console_scripts": [
            "base64-to-image-files = pre_commit_nb.base64_to_image_files:main",
            "base64-to-external-storage = pre_commit_nb.base64_to_external_storage:main"  # NOQA E501
        ]
    }
)
