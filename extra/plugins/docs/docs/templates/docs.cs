<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<h1>Documents</h1>
<ul>
<?cs each:item = pdfs ?>
    <li><?cs var:item ?> (<a href="docs/pdf/<?cs var:item ?>.pdf">PDF</a>) (<a href="docs/html/<?cs var:item ?>/<?cs var:item ?>.html">HTML</a>)</li>
<?cs /each ?>
</ul>

<h1>IRC Logs</h1>
<ul>
<?cs each:item = irc ?>
     <li><a href="docs/irc/<?cs var:item ?>"><?cs var:item ?></a></li>
<?cs /each ?>
</ul>

<?cs include "footer.cs" ?>
