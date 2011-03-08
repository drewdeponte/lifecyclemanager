<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav"></div>

<h1>Revision log for <?cs var:user ?></h1>

<div id="content" class="wiki">
<div class="wikipage">

<div class="wiki-toc">
Ranges
<ol>
<?cs each:link = changeset_links ?>
  <li><a href="<?cs var:link['href'] ?>"><?cs var:link['title'] ?></a><br/></li>
<?cs /each ?>
</ol>
<br/>
On this page
<ol>
<?cs each:link = toc_links ?>
  <li><a href="#<?cs var:link['anchor'] ?>"><?cs var:link['title'] ?></a></li>
<?cs /each ?>
</ol>
</div>


<?cs each:changeset = changesets ?>
    <p>
    <a name="<?cs var:changeset[0] ?>">Revision <?cs var:changeset[0] ?> @ <?cs var:changeset[1] ?></a><br/>
    <?cs var:changeset[2] ?>
    <?cs each:change = changeset[3] ?>
      <?cs var:change[0] ?>
      <?cs if:change[1] ?>
        <pre class="diff">
        <?cs var:change[1] ?>
        </pre>
      <?cs else ?>
        <br/>
      <?cs /if ?>
    <?cs /each ?>
    </p>
    <hr/>
<?cs /each ?>

</div> <!-- class="wikipage" -->
</div> <!-- id="content" class="wiki" -->

<?cs include "footer.cs" ?>
