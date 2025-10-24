---
name: Newsletter subscription
description: Dodaj nowego subskrybenta do Machine Cinema AI Newsletter
labels:
  - subscribe
title: "Subscribe: <email>"
body:
  - type: markdown
    attributes:
      value: |
        Dziękujemy za chęć dołączenia do naszego dziennego newslettera AI. Wypełnij pola poniżej.
  - type: input
    id: email
    attributes:
      label: Email address
      description: Adres, na który będziemy wysyłać newsletter.
      placeholder: osoba@example.com
    validations:
      required: true
  - type: input
    id: name
    attributes:
      label: Name (optional)
      description: Jeżeli chcesz, podaj imię i nazwisko.
      placeholder: Jan Kowalski
    validations:
      required: false
  - type: textarea
    id: source
    attributes:
      label: How did you hear about us?
      description: Krótkie info o źródle (opcjonalne).
      placeholder: Poleć nas znajomym! ;)
    validations:
      required: false
  - type: checkboxes
    id: consent
    attributes:
      label: Confirm subscription
      options:
        - label: Zgadzam się na otrzymywanie newslettera drogą mailową.
          required: true
