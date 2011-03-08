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

  <div id="ctxtnav" class="nav">
    <h2>Requirement Navigation</h2>
    <ul><?cs
      if:trac.acl.REQUIREMENT_CREATE ?><li class="first"><a href="<?cs
        var:requirement.add_requirement_href ?>">Add Requirement</a></li><?cs
      /if ?><?cs
      if:trac.acl.REQUIREMENT_ADMIN ?><li class="last"><a href="<?cs
        var:trac.href.editdict ?>">Edit Functional Primitives</a></li><?cs
      else ?><a href="<?cs var:trac.href.editdict ?>">View Functional
        Primitives</a></li><?cs
      /if ?>
    </ul>
  </div>

<div id="content">
<h1> Requirement Dashboard </h1>

<div id="graph_dash_overall">
  <h2>Dashboard Overall Graph</h2>
  <p>This graph shows a summary of the project by its requirements.</p>
  <ul><h6>
  <li> Yellow Bars = Number of Changes to Requirements </li>
  <li> Blue Line =  Total Number of Active Requirements </li>
  <li> Red Lines = Milestones </li>
  <li>Green Triangles = Validation Points</li>
  </ul></h6>
  <iframe src="<?cs var: graph_path ?>/dash_overall" height="525" width="525" 
  scrolling="auto" frameborder="0"></iframe>
</div>

<div id="report">
  <h2> Requirement Reports </h2>
  <a href="<?cs var:report_href ?>">Available Reports</a>
  <ul><?cs
  each group =  rlist?>
    <li><a href="<?cs var:requirement_href ?>/<?cs var:group.1 ?>"><?cs 
    var:group.0 ?></a></li><?cs
  /each ?></ul>
</div>


<div id="validation">
  <h2> Requirement Validation </h2><?cs
  if:current_val == #1 ?>
    The current set of requirements has been validated.<br />
    Most recent Validation on <?cs var:recent_val_date ?>.<?cs
  else ?>
    The current set of requirements <b>has not</b> been validated. <br /><?cs
    if:recent_val_date != #1 ?> Last validation was on 
      <?cs var:recent_val_date ?>.<br /><?cs
    /if ?><?cs
    if:show_val_report.1 == #1 ?>
     There are <a href="<?cs var:req_changed_href ?>"> requirements 
     that have been changed or added.</a><br /><?cs
    /if ?><?cs
    if:show_val_report.0 == #1 ?>
      There are <a href="<?cs var:req_ood_href ?>">out-of-date 
      requirements</a>.<?cs
    /if ?><?cs
  /if ?>
</div>

<div id="graph_component_req_count">
    <h2> Relative Component sizes based on requirements </h2>
    <iframe src="<?cs var: graph_path ?>/component_req_count" height="420" width="525" scrolling="auto" frameborder="0"></iframe>
</div>

<div id="graph_dash_pie">
    <h2> Ticket Pie Chart </h2>
    <p> This graph shows the percentage of requirements with certain types of associated tickets.</p>
    <ul><h6>
    <li> Open - requirements with any open tickets </li>
    <li> Closed - requirements with all closed tickets </li>
    <li> None - requirements with no associated tickets </li>
    </ul></h6>
    <iframe src="<?cs var: graph_path ?>/dash_pie" height="400" width="400" scrolling="auto" frameborder="0"></iframe>
</div>
    
</div><!--- This is the closing div for content --->
<?cs include "footer.cs" ?>
