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
<script type="text/javascript">
    function toggleShow(show,hide) {
        document.getElementById(hide).style.display = 'none';
        document.getElementById(show).style.display = 'block';
        document.getElementById(show).focus();
        return;
    }
    function storeText(str,field, text){
        document.getElementById(text).innerHTML=str;
        toggleShow(text,field);
        return;
    }
</script>

<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

  <div id="ctxtnav" class="nav">
    <h2>Requirement Navigation</h2>
    <ul><li class="first"><?cs
      if:chrome.links.top.0.href ?><a href="<?cs
        var:chrome.links.top.0.href ?>">Available Reports</a><?cs
      else ?>Available Reports<?cs
      /if ?></li><?cs
      if:requirement.add_requirement_href ?><li class="last"><a href="<?cs
        var:requirement.add_requirement_href ?>">Add Requirement</a></li><?cs
      /if ?>
    </ul>
  </div>

<div id="content">

<div id="mheader">
  <h1><?cs
  var:editdict.title ?></h1><?cs

        if:trac.acl.REQUIREMENT_ADMIN ?><h5>Editing the status of Functional
        Primitives or Objects can cause the requirements that rely on them
        to go out of date.  You must reset the status of any out of date 
        requirements (to enabled or disabled) in order to validate.
        </h5><?cs 
        /if ?>
</div>

<div id="sidebar">
  <ul>
  <li><a href="<?cs var:editdict.href_admin ?>">Admin Settings</a></li>
  <li><a href="<?cs var:editdict.href_object ?>">View Objects</a></li>
  <li><a href="<?cs var:editdict.href_fp ?>">View Functional Primitives</a></li>
  </ul>
</div>

<?cs if:editdict.show == "object" ?>
  <div id="object" class="itemlist">
  <h2>Objects</h2><?cs
    if: editdict.empty != #0 ?>
    <form id= "editobj"  method="post" 
    action="<?cs var:editdict.href_object ?>">
      <table class="list"><tr><td>Status</td><td>Object</td><td>Description</td></tr><?cs 
      each group = editdict.values ?><tr><td class="status">
        <input type="checkbox" <?cs
        if:group.status == "enabled" ?> checked <?cs
        /if ?> name="status_<?cs var:group.name ?>" /></td><td class="name">
        <span id="<?cs var:group.name ?>_id" onclick="toggleShow('<?cs var:group.name ?>_form','<?cs var:group.name ?>_id')">
        <?cs var:group.name ?> </span>
        <input id="<?cs var:group.name ?>_form" class="hidden" type="text" 
        name="change_obj_<?cs var:group.name ?>" 
        value="<?cs var:group.name ?>" onblur="storeText(this.value,'<?cs var:group.name ?>_form','<?cs var:group.name ?>_id')" /></td>
        <td class="description">
        <textarea id="<?cs var:group.name ?>_dfield" class="hidden" 
        cols="30" rows="5" 
        name="change_desc_<?cs var:group.name ?>"
        onblur="storeText(this.value,'<?cs var:group.name ?>_dfield','<?cs var:group.name ?>_desc')" ><?cs var:group.description ?></textarea>
        <span id="<?cs var:group.name ?>_desc" onclick="toggleShow('<?cs var:group.name ?>_dfield','<?cs var:group.name ?>_desc')">
        <?cs var:group.description ?> </span>
        </td></tr><?cs
        /each ?></table>
    <input type="hidden" name="obj_state_dict" 
    value="<?cs var:obj_dict.encoded ?>" />
    <input type="submit" name="submit_mod_obj" value="Save Changes" />
    </form><?cs
    else ?> There are no objects to display.<?cs
    /if ?>
  </div>

  <?cs if:trac.acl.REQUIREMENT_ADMIN ?> 
  <div id="newobj" class="newitem">
      <form id="new_obj" method="post" 
      action="<?cs var:editdict.href_object  ?>">
      <fieldset><legend>New Object</legend>
        <p>Add a new object.</p>
        <table class="properties">
        <tr><td> Name: <br /> <input name="newobjname" type="text" /></td></tr>
        <tr><td>Description: <br />
            <textarea cols="50" rows="6" name="newobjdesc"></textarea></td>
        </tr>
        <tr><td><input type="submit" name="submit_new_obj" 
                value="Submit Object" />
        </td></tr></td>
        </table>
      </fieldset>
    </form>
  </div><?cs
  /if ?><?cs
/if ?>

<?cs if:editdict.show == "fphyps" ?>
  <div id="fphyponym" class="itemlist">
  <h2>Funtional Primitives</h2><?cs
      if editdict.empty != #0 ?>
      <form id="mod_fp" method="post" 
      action="<?cs var:editdict.href_fp ?>" ><?cs 
      each group = editdict.values ?>
        <input type="checkbox" <?cs if:group.fp.1 == "enabled" ?> checked <?cs
        /if ?> name ="status_fp_<?cs var:group.fp.0 ?>"/><?cs
        var:group.fp.0 ?><input type="text" 
        name="change_fp_<?cs var:group.fp.0 ?>" /> 
        Swap with <select name="swap_<?cs var:group.fp.0 ?>">
        <option selected> hyponym</option><?cs 
        each hyp = group.hyponyms ?>
          <option><?cs var:hyp.0 ?></option><?cs
        /each ?></select><br />
        Description: <?cs var:group.description ?><br /> 
        <textarea cols="30" rows="5" 
        name="change_desc_<?cs var:group.fp.0 ?>"><?cs var:group.description ?></textarea><br />
        Hyponyms: <ul>
        <li>Add Hyponym: <input type="text" 
        name="new_hyp_<?cs var:group.fp.0 ?>" /></li><?cs
        each hyp = group.hyponyms ?><li>
          <input type="checkbox" <?cs if:hyp.1 == "enabled" ?> checked <?cs
          /if ?> name="status_hyp_<?cs var:hyp.0 ?>" /><?cs
          var:hyp.0 ?> <input type="text" 
                       name="change_hyp_<?cs var:hyp.0 ?>" /></li><?cs
        /each ?></ul><?cs
      /each ?>
    </table>
    <input type="hidden" name="fp_state_dict"
    value="<?cs var:fp_dict.encoded ?>" />
    <input type="submit" name="submit_mod_fphyp" value="Apply Changes" />
    </form><?cs
    else ?>There are no functional primitives to display.<?cs
    /if ?>
  </div>

  <?cs if:trac.acl.REQUIREMENT_ADMIN ?> 
  <div id="newfp" class="newitem">
      <form id="new_dict_item" method="post" 
      action="<?cs var:editdict.href_fp  ?>">
      <fieldset><legend>New Functional Primitive</legend>
        <p>Add a new fp. If you are adding multiple hyponyms, separate them
        with commas.</p>
        <table class="properties">
        <tr><td> Name: <br /> <input name="newfp" type="text" /></td></tr>
        <tr><td>Hyponyms: <br /><input name="newfphyps" type="text" /></td></tr>
        <tr><td>Description: <br />
            <textarea cols="50" rows="6" name="newfpdesc"></textarea></td>
        </tr>
        <tr><td><input type="submit" name="submit_new_fp" 
                value="Submit Functional Primitive" /></td></tr>
        </table>
      </fieldset>
    </form></td><?cs
  /if ?>
  </div><?cs
/if ?>

<?cs if:editdict.show == "admin" ?>
  <div id="adminsettings">
    <h2>Settings<h2>
      <form id="admin_on_the_fly" method="post"
       action="<?cs var:editdict.href_admin ?>">
       <fieldset><legend>Admin Options</legend>
          <p>When "on-the-fly" creation is disabled for functional primitives or
          objects, users must use existing functional primitives or objects
          when creating new requirements.</p>
          <input type="checkbox" name="fp_on_fly_enable" <?cs
          if: fp_enabled == "enabled" ?> checked <?cs
          /if ?>/>
          Enable "on-the-fly" creation of functional primitives <br />
          <input type="checkbox" name="object_on_fly_enable" <?cs
          if: object_enabled == "enabled" ?>  checked <?cs
          /if ?>/>
          Enable "on-the-fly" creation of objects <br />
          <input type="submit" name="submit_admin_settings" 
                value="Submit Admin Settings" />
</fieldset>
    </form>
  </div><?cs
/if ?>



</div>

<?cs include "footer.cs" ?> 
