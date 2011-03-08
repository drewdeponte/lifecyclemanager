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
 <h2>Report Navigation</h2>
 <ul><li class="first"><?cs
   if:chrome.links.up.0.href ?><a href="<?cs
    var:chrome.links.up.0.href ?>">Available Reports</a><?cs
   else ?>Available Reports<?cs
  /if ?></li><?cs
  if:report.query_href ?><li><a href="<?cs
   var:report.query_href ?>">Custom Query</a></li><?cs
  /if ?>
  <?cs
    if:report.add_requirement_href ?><li><a href="<?cs
      var:report.add_requirement_href ?>">Add Requirement</a></li><?cs
    /if ?>
  <?cs
    if:report.edit_fphyp_href ?><?cs 
      if:trac.acl.REQUIREMENT_ADMIN ?><li class="last"><a href="<?cs
        var:report.edit_fphyp_href ?>">Edit Functional Primitives</a></li><?cs
      else ?><a href="<?cs var:report.edit_fphyp_href ?>">View Functional 
      Primitives</a></li><?cs
      /if ?><?cs
    /if ?>
 </ul>
</div>

<?cs if $report.is_all_reqs_report == 1 ?>
 <form method="post" action="" >
  <table><tr>
      <?cs if $report.validate == 2 ?>
    <td>Requirements Validated (<?cs var:report.latest_validation ?>)</td>
   <?cs else ?>
   
    <?cs if $report.validate == 1 ?>
    <td>Requirments cannot be validated. Out of date requirements exist.</td>
   <?cs else ?>
     
    <?cs if $report.currently_validated == 0 ?>
     <td><h5> Need to validate current set of requirements: </h5></td>
     <td><input type="submit" name="ValidateSubmit" value="Validate" title="Validate" /></td>  
    <?cs else ?>
     <td>Current set of requirements validated</td>
    <?cs /if ?>
    </tr><tr><td><h6> Most recent validation: <?cs var:report.latest_validation ?> </h6></td>
    <td><h6> Note: any change to the requirement set will neccesitate re-validation of the set</td></h6>
   <?cs /if ?><?cs /if ?></tr>
  </table>
 </form>
 <hr />
<?cs /if ?>

<div id="content" class="report">

 <?cs def:report_hdr(header) ?>
   <?cs if $header ?>
     <?cs if idx > 0 ?>
       </table>
     <?cs /if ?>
   <?cs /if ?>
   <?cs if:header ?><h2><?cs var:header ?></h2><?cs /if ?>
   <?cs if $report.id == -1 ?>
     <table class="listing reports">
   <?cs else ?>
     <table class="listing requirements">
   <?cs /if ?>
    <thead>
     <tr>
       <?cs set numcols = #0 ?>
       <?cs each header = report.headers ?>
         <?cs if $header.fullrow ?>
           </tr><tr><th colspan="100"><?cs var:header ?></th>
         <?cs else ?>
           <?cs if $report.sorting.enabled ?>
             <?cs set vars='' ?>
             <?cs each arg = report.var ?>
               <?cs set vars = vars + '&amp;' + name(arg) + '=' + arg ?>
             <?cs /each ?>
             <?cs set sortValue = '' ?>
             <?cs if $header.asc == '1' ?>
               <?cs set sortValue = '?sort='+$header.real+'&amp;asc=0' ?>
             <?cs else ?>
               <?cs set sortValue = '?sort='+$header.real+'&amp;asc=1' ?>
             <?cs /if ?>
             <?cs if $header ?>
             <th><a href="<?cs var:sortValue ?><?cs var:vars ?>"><?cs var:header ?></a></th>
             <?cs /if ?>
           <?cs elif $header ?>
             <th><?cs var:header ?></th>
           <?cs /if ?>
           <?cs if $header.breakrow ?>
              </tr><tr>
           <?cs /if ?>
         <?cs /if ?>
         <?cs set numcols = numcols + #1 ?>
       <?cs /each ?>
     </tr>
    </thead>
 <?cs /def ?>

 <?cs def:report_5_hdr(header, header_link) ?>
   <?cs if $header ?>
     <?cs if idx > 0 ?>
       </table>
     <?cs /if ?>
   <?cs /if ?>
   <?cs if:header ?><h3><a title="Requirement" href="<?cs var:header_link ?>">
   <?cs var:header ?></a></h3><?cs /if ?>
   <?cs if $report.id == -1 ?>
     <table class="listing reports">
   <?cs else ?>
     <table class="listing requirements">
   <?cs /if ?>
    <thead>
     <tr>
       <?cs set numcols = #0 ?>
       <?cs each header = report.headers ?>
         <?cs if $header.fullrow ?>
           </tr><tr><th colspan="100"><?cs var:header ?></th>
         <?cs else ?>
           <?cs if $report.sorting.enabled ?>
             <?cs set vars='' ?>
             <?cs each arg = report.var ?>
               <?cs set vars = vars + '&amp;' + name(arg) + '=' + arg ?>
             <?cs /each ?>
             <?cs set sortValue = '' ?>
             <?cs if $header.asc == '1' ?>
               <?cs set sortValue = '?sort='+$header.real+'&amp;asc=0' ?>
             <?cs else ?>
               <?cs set sortValue = '?sort='+$header.real+'&amp;asc=1' ?>
             <?cs /if ?>
             <?cs if $header ?>
             <th><a href="<?cs var:sortValue ?><?cs var:vars ?>"><?cs var:header ?></a></th>
             <?cs /if ?>
           <?cs elif $header ?>
             <th><?cs var:header ?></th>
           <?cs /if ?>
           <?cs if $header.breakrow ?>
              </tr><tr>
           <?cs /if ?>
         <?cs /if ?>
         <?cs set numcols = numcols + #1 ?>
       <?cs /each ?>
     </tr>
    </thead>
 <?cs /def ?>

 <?cs def:report_cell(class,contents) ?>
   <?cs if $cell.fullrow ?>
     </tr><tr class="<?cs var:row_class ?>" style="<?cs var: row_style ?>;border: none; padding: 0;">
      <td class="fullrow" colspan="100">
       <?cs var:$contents ?><hr />
      </td>
   <?cs else ?>
   <td <?cs if $cell.breakrow || $col == $numcols ?>colspan="100" <?cs /if
 ?>class="<?cs var:$class ?>"><?cs if $contents ?><?cs var:$contents ?><?cs /if ?></td>
 
 <?cs if $cell.breakafter ?>
     </tr><tr class="<?cs var: row_class ?>" style="<?cs var: row_style ?>;border: none; padding: 0">
 <?cs /if ?>
   <?cs /if ?>
   <?cs set col = $col + #1 ?>
 <?cs /def ?>
 
 <?cs set idx = #0 ?>
 <?cs set group = '' ?>
 <?cs set h_link = '' ?>
 
 <?cs if:report.mode == "list" ?>
  <h1><?cs var:title ?><?cs
   if:report.numrows && report.id != -1 ?><span class="numrows"> (<?cs
    var:report.numrows ?> matches)</span><?cs
   /if ?></h1><?cs
   if:report.description ?><div id="description"><?cs
    var:report.description ?></div><?cs
   /if ?>

     <?cs each row = report.items ?>
       <?cs if group != row.__group__ || idx == #0 ?>
         <?cs if:idx != #0 ?></tbody><?cs /if ?>
         <?cs set group = row.__group__ ?>
         <?cs if report.report == 5 ?>
           <?cs set h_link = row.__link__ ?>
           <?cs call:report_5_hdr(group, h_link) ?>
         <?cs else ?>
           <?cs call:report_hdr(group) ?>
         <?cs /if ?>
         <tbody>
       <?cs /if ?>

       <?cs if row.__color__ ?>
         <?cs set rstem='color'+$row.__color__ +'-' ?>
       <?cs else ?>
        <?cs set rstem='' ?>
       <?cs /if ?>
       <?cs if idx % #2 ?>
         <?cs set row_class=$rstem+'even' ?>
       <?cs else ?>
         <?cs set row_class=$rstem+'odd' ?>
       <?cs /if ?>

       <?cs set row_style='' ?>
       <?cs if row.__bgcolor__ ?>
         <?cs set row_style='background: ' + row.__bgcolor__ + ';' ?>
       <?cs /if ?>
       <?cs if row.__fgcolor__ ?>
         <?cs set row_style=$row_style + 'color: ' + row.__fgcolor__ + ';' ?>
       <?cs /if ?>
       <?cs if row.__style__ ?>
         <?cs set row_style=$row_style + row.__style__ + ';' ?>
       <?cs /if ?>

       <tr class="<?cs var: row_class ?>" style="<?cs var: row_style ?>">
       <?cs set idx = idx + #1 ?>
       <?cs set col = #0 ?>
       <?cs each cell = row ?>
         <?cs if report.report == 5 ?>
           <?cs if cell.hidden || cell.hidehtml ?>
           <?cs elif name(cell) == "ticket" ?>
             <?cs call:report_cell('ticket',
                                   '<a title="View ticket" href="'+
                                   $cell.ticket_href+'">'+$cell+'</a>') ?>
             <?cs elif name(cell) == "summary" && cell.ticket_href ?>
               <?cs call:report_cell('summary', '<a title="View ticket" href="'+
                                     $cell.ticket_href+'">'+$cell+'</a>') ?>
             <?cs elif name(cell) == "Description" && cell.requirement_href ?>
               <?cs call:report_cell('Description', $cell.parsed) ?>
           <?cs /if ?>
         <?cs else ?>
           <?cs if cell.hidden || cell.hidehtml ?>
           <?cs elif name(cell) == "Requirement" ?>
             <?cs call:report_cell('Requirement',
                                   '<a title="View requirement" href="'+
                                   $cell.requirement_href+'">'+$cell+'</a>') ?>
           <?cs elif name(cell) == "Wiki" ?>
             <?cs call:report_cell('Wiki',
                                   '<a title="View wiki" href="'+
                                   $cell.wiki_href+'">'+$cell+'</a>') ?>
           <?cs elif name(cell) == "ticket" ?>
             <?cs call:report_cell('ticket',
                                   '<a title="View ticket" href="'+
                                   $cell.ticket_href+'">'+$cell+'</a>') ?>
           <?cs elif name(cell) == "summary" && cell.ticket_href ?>
             <?cs call:report_cell('summary', '<a title="View ticket" href="'+
                                   $cell.ticket_href+'">'+$cell+'</a>') ?>
           <?cs elif name(cell) == "Description" && cell.requirement_href ?>
             <?cs call:report_cell('Description', $cell.parsed) ?>
           <?cs elif name(cell) == "report" ?>
             <?cs call:report_cell('report',
                  '<a title="View report" href="'+$cell.report_href+'">{'+ idx +'}</a>') ?>
             <?cs set:report_href=$cell.report_href ?>
           <?cs elif name(cell) == "time" ?>
             <?cs call:report_cell('date', $cell.date) ?>
           <?cs elif name(cell) == "date" || name(cell) == "created" || name(cell) == "modified" ?>
             <?cs call:report_cell('date', $cell.date) ?>
           <?cs elif name(cell) == "datetime"  ?>
             <?cs call:report_cell('date', $cell.datetime) ?>
           <?cs elif name(cell) == "title" && cell.report_href?>
             <?cs call:report_cell('title',
                                   '<a  title="View report" href="'+
                                   $cell.report_href+'">'+$cell+'</a>') ?>
           <?cs else ?>
             <?cs call:report_cell(name(cell), $cell) ?>
           <?cs /if ?>
         <?cs /if ?>
       <?cs /each ?>
       </tr>
     <?cs /each ?>
    </tbody>
   </table><?cs
   if report.message ?>
    <div class="system-message"><?cs var report.message ?></div><?cs
   elif:idx == #0 ?>
    <div id="report-notfound">No matches found.</div><?cs
   /if ?>
  <?cs /if ?>

 </div>
<?cs include "footer.cs" ?>
