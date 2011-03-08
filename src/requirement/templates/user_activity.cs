<?cs
# Copyright 2007-2008 Lifecycle Manager Development Team
# http://www.insearchofartifice.com/lifecyclemanager/wiki/DevTeam
#
# This file is part of Lifecycle Manager.
#
# Lifecycle Manager is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Lifecycle Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Lifecycle Manager.  If not, see
# <http://www.gnu.org/licenses/>.
?>

<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="debug"><?cs var: debug  ?></div>

<?cs def:create_link(rep_req, link_req) ?>
    <a href="<?cs var: link_requirement_href ?>/<?cs var: $link_req  ?>">
        <?cs var: $rep_req ?>
    </a>
<?cs /def ?>

<div id="ctxtnav" class="nav">
 <h2>Report Navigation</h2>
 <ul><li class="first"><?cs
   if:chrome.links.up.0.href ?><a href="<?cs
    var:chrome.links.up.0.href ?>">Available Reports</a><?cs
   else ?>Available Reports<?cs
  /if ?></li><?cs
  if:report.query_href ?><li class="last"><a href="<?cs
   var:report.query_href ?>">Custom Query</a></li><?cs
  /if ?>
  <?cs
    if:report.add_requirement_href ?><li class="last"><a href="<?cs
      var:report.add_requirement_href ?>">Add Requirement</a></li><?cs
    /if ?>
 </ul>
</div>

<div id="content" class="timeline">

<h1>Per user history of changes for username "<?cs var:username ?>" </h1>

 

<form id="prefs" method="get" action="<?cs var:trac.href.requirements.view.8 ?>">
 <div>
  <label>View changes for user <input type="text" size="14" name="username"
   value="<?cs var:username ?>" /></label>.
 </div>
 <fieldset>
   <?cs if: twiki ?>
    <label><input type="checkbox" name="wiki" checked="checked" value="1"> Show Wiki activity</label><br>
   <?cs else ?>
    <label><input type="checkbox" name="wiki" value="0"> Show Wiki activity</label><br>
   <?cs /if ?>

   <?cs if: trequirement ?>
    <label><input type="checkbox" name="requirement" checked="checked" value="1"> Show Requirement activity</label><br>
   <?cs else ?>
    <label><input type="checkbox" name="requirement" value="0"> Show Requirement activity</label><br>
   <?cs /if ?>

   <?cs if: tticket ?>
    <label><input type="checkbox" name="ticket" checked="checked" value="1"> Show Ticket activity</label><br>
   <?cs else ?>
    <label><input type="checkbox" name="ticket" value="0"> Show Ticket activity</label><br>
   <?cs /if ?>

 </fieldset>
 <div class="buttons">
  <input type="submit" name="Search" value="Update"/>
 </div>
</form>
<?cs if: !noresults ?>
<?cs
 def:day_separator(date) ?><?cs
  if:date != current_date ?><?cs
   if:current_date ?></dl><?cs /if ?><?cs
   set:current_date = date ?>
   <h2><?cs var:date ?>:</h2><dl><?cs
  /if ?><?cs
 /def ?><?cs
 each:event = requirements.view.8.events ?><?cs var:event ?><?cs
  call:day_separator(event.date) ?><dt class="<?cs
  var:event.kind ?>"><a href="<?cs var:event.href ?>"><?cs var:event.kind ?>: <span class="time"><?cs
  var:event.time ?></span> <?cs var:event.title ?></a></dt><?cs
   if:event.message ?><dd class="<?cs var:event.kind ?>"><?cs
    var:event.message ?></dd><?cs
   /if ?><?cs
 /each ?><?cs
 if:len(requirements.view.8.events) ?></dl>
<?cs /if ?>

<?cs else ?>
 <p>No Matches Found</p>
<?cs /if ?>
</div>
<?cs include "footer.cs" ?>
