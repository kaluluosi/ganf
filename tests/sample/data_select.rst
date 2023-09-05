.. highlight:: pycon+sql

.. |prev| replace:: :doc:`data_insert` 
.. |next| replace:: :doc:`data_update` 

.. include:: tutorial_nav_include.rst

.. _tutorial_selecting_data:

.. rst-class:: core-header, orm-dependency

Using SELECT Statements
-----------------------

For both Core and ORM, the :func:`_sql.select` function generates a
:class:`_sql.Select` construct which is used for all SELECT queries.
Passed to methods like :meth:`_engine.Connection.execute` in Core and
:meth:`_orm.Session.execute` in ORM, a SELECT statement is emitted in the
current transaction and the result rows available via the returned
:class:`_engine.Result` object.

.. container:: orm-header

    **ORM Readers** - the content here applies equally well to both Core and ORM
    use and basic ORM variant use cases are mentioned here.  However there are
    a lot more ORM-specific features available as well; these are documented
    at :ref:`queryguide_toplevel` .


The select() SQL Expression Construct
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :func:`_sql.select` construct builds up a statement in the same way
as that of :func:`_sql.insert` , using a :term:`generative` approach where
each method builds more state onto the object.  Like the other SQL constructs,
it can be stringified in place::

    >>> from sqlalchemy import select
    >>> stmt = select(user_table).where(user_table.c.name == "spongebob")
    >>> print(stmt)
    {printsql}SELECT user_account.id, user_account.name, user_account.fullname
    FROM user_account
    WHERE user_account.name = :name_1

Also in the same manner as all other statement-level SQL constructs, to
actually run the statement we pass it to an execution method.
Since a SELECT statement returns
rows we can always iterate the result object to get :class:`_engine.Row` 
objects back:

.. sourcecode:: pycon+sql

    >>> with engine.connect() as conn:
    ...     for row in conn.execute(stmt):
    ...         print(row)
    {execsql}BEGIN (implicit)
    SELECT user_account.id, user_account.name, user_account.fullname
    FROM user_account
    WHERE user_account.name = ?
    [...] ('spongebob',){stop}
    (1, 'spongebob', 'Spongebob Squarepants')
    {execsql}ROLLBACK{stop}

When using the ORM, particularly with a :func:`_sql.select` construct that's
composed against ORM entities, we will want to execute it using the
:meth:`_orm.Session.execute` method on the :class:` _orm.Session`; using
this approach, we continue to get :class:`_engine.Row` objects from the
result, however these rows are now capable of including
complete entities, such as instances of the ``User`` class, as individual
elements within each row:

