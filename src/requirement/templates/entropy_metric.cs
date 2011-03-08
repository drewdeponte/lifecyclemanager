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

<h1>Entropy Metric</h1>
    <div id="description">
        <p>Calculate information entropy of requirements</p>


<?cs if: !noresults ?>
	<div id="reqs_entropy">
	<table>
	     <tr>
	     <th>Requirement</th>
	     <th>Entropy</th>
	     </tr>
	<?cs each:req = reqs ?>
	     <tr>
	     <td><a title="View requirement" href="<?cs var:req["link"] ?>"><?cs var:req["name"] ?></a></td>
	     <td style="text-align: center"><?cs var:req["entropy"] ?></td>
	     </tr>
	<?cs /each ?>
	</table>
	</div>

	<div id="components_entropy">
	<table>
	     <tr>
	     <th>Component</th>
	     <th>Relative entropy</th>
	     </tr>
	<?cs each:comp = components ?>
	     <tr>
	     <td><?cs var:comp["name"] ?></td>
	     <td style="text-align: center"><?cs var:comp["percent"]?>%</td>
	     </tr>
	<?cs /each ?>
	</table>
	</div>
    <div id="entropy_graph">
        <h3>Entropy of the Project over Time</h3>
        <h6>Red lines represent Milestone due-dates</h6>
        <iframe src="<?cs var: graph_path ?>entropy_graph" height="420" 
         width="420" scrolling="auto" frameborder="0"></iframe>
    </div>
    </div>
<?cs else ?>
    <p>No Matches Found</p>
<?cs /if ?>

<?cs include "footer.cs" ?>
