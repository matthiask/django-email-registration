=========================
django-email-registration
=========================

The eleventy-eleventh email registration app for Django.

But this one does not feed your cat.

.. image:: https://travis-ci.org/matthiask/django-email-registration.png?branch=master
   :target: https://travis-ci.org/matthiask/django-email-registration


Usage
=====

This example assumes you are using a recent version of Django, jQuery and
Twitter Bootstrap.

1. Install ``django-email-registration`` using pip.

2. Copy this code somewhere on your login or registration page::

    <h2>{% trans "Send an activation link" %}</h2>
    <form method="post" action="{% url "email_registration_form" %}"
        class="well" id="registration">
      {% csrf_token %}
      <div class="controls">
        <input id="id_email" type="text" name="email" maxlength="75"
          placeholder="{% trans "Email address" %}">
        <!--input id="id_next" type="hidden" name="next" maxlength="75"
          value="/mypath/"-->
      </div>
      <button type="submit" class="btn btn-primary">
        {% trans "Register" %}</button>
    </form>

    <script>
    function init_registration($) {
      $('#registration').on('submit', function() {
        var $form = $(this);
        $.post(this.action, $form.serialize(), function(data) {
          $('#registration').replaceWith(data);
          init_registration($);
        });
        return false;
      });
    }
    $(init_registration);
    </script>

   (Alternatively, include the template snippet
   ``registration/email_registration_include.html`` somewhere.)

   The ``next`` field is optional and is passed to the ``auth.login`` view.

3. Add ``email_registration`` to ``INSTALLED_APPS`` and include
   ``email_registration.urls`` somewhere in your URLconf.

   Make sure Django can send emails.

4. Presto.
