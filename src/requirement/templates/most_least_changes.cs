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

<h1>Most To Least Changed Requirements</h1>
    <div id="description">
        <p>Show the most to least changed requirements</p>
    </div>
<?cs if: noresults ?>
    <p>No Matches Found</p>
<?cs else ?>
    <table class="listing requirements">
        <?cs each: requirement = requirements ?> 
            <tr>
                <td width="1">
                    <nobr>
                        <?cs call:create_link(requirement.0, requirement.2) ?>
                    </nobr>
                </td>
                <td width="1">[<?cs var: requirement.1 ?>]</td>
                <td><img src="<?cs var: graph_path ?><?cs var: requirement.2  ?>/mls_<?cs var: requirement.1 ?>" alt="Graph" /></td>
            </tr>
        <?cs /each ?>
    </table>
<?cs /if ?>

<?cs include "footer.cs" ?>
