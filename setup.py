from setuptools import setup, find_packages

setup(
    name='llm_agents',
    version='0.1.0',
    description='A package for building agents which use the OpenAI API to figure out actions to take and can use tools.',
    author='Marc Päpper',
    author_email='marc@paepper.com',
    url='https://github.com/mpaepper/llm_agents',
    packages=find_packages(),
    install_requires=[
        'google-search-results>=2.4.2',
        'openai>=0.27.0',
        'pydantic>=1.10.5',
        'requests>=2.28.2'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License'
    ],
)
