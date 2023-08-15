# Introduction

Zenpy uses Betamax recordings to speed up daily tests. Therefore, there are two testing modes - using records and with a live Zendesk account.

Now you can use two unittest libraries - nose or pytest:

~~~
# pip install -r requirements.dev
~~~

Nose is obsolete and doesn't work with Python 3.9+. 

Pytest supports Python 2.7 until version 4.6.

# Using recordings

You don't need any other things for using recordings.
~~~
# cd /dir/zenpy
# make unittest
or
# make pytest
~~~

Partial testing:

~~~
# nosetests -v --stop --exe tests/test_api/test_create_update_delete_zendesk.py
# nosetests -v --stop --exe tests/test_api/test_create_update_delete_zendesk.py:TestUserCreateUpdateDelete
# nosetests -v --stop --exe tests/test_api/test_create_update_delete_zendesk.py:TestUserCreateUpdateDelete.test_multiple_update_full_objects

or
# pytest tests/test_api/test_create_update_delete_zendesk.py::TestUserCreateUpdateDelete.test_multiple_update_full_objects
~~~

# Testing on a live account

To test on a live account you need to carry out the steps below:

1. Put **zenpy-test-credentials.json** to a home directory (~).
2. Delete all files in **./tests/test_api/betamax/**.
3. Then start testing as usual.
4. If a test fails, delete its files in betamax before restarting.

~~~ 
zenpy-test-credentials.json:

{
        "subdomain": "subdomain",
        "email": "email",
        "token": "token"
}
~~~

To pass all the tests successfully, please provide some things:

1. In **./zenpy/cache.py:ZenpyCacheManager.__init__** temporary change ttl for ticket cache to 300. Some tests take too much time and fail on expired cache elements.
2. In **./zenpy/tests/test_api/test_incremental_object_update.py:TestIncrementalObjectUpdate.setUp** provide an existing ticket id.
3. In **./zenpy/tests/test_api/test_webhooks_api.py:TestWebhooks.test_invocations** and **.test_invocation_attempts** put a real webhook id with a non-empty list of invocations.
4. Please do not commit these changes to the main repository.

Notes:

* Testing webhooks on a live account may take a lot of time and could result with an error because of rate limits. Consider to test it separately.
