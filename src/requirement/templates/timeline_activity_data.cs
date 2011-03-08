<data 
  wiki-url="<?cs var: event_url ?>" 
  wiki-section="<?cs var: event_section ?>">
  <?cs each: event = events ?>
    <event
    <?cs each: element = event ?>
      <?cs if: name(element) != 'data' ?>
        <?cs name: element ?>="<?cs var: element ?>"
      <?cs /if ?>
    <?cs /each ?>>
      <?cs var: event.data.message ?>
    </event>
  <?cs /each ?>
</data>