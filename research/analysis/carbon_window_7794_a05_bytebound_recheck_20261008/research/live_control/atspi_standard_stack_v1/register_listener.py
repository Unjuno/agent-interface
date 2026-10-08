#!/usr/bin/env python3
import ctypes as C, ctypes.util, json, sys, time

class GError(C.Structure):
    _fields_=[('domain',C.c_uint),('code',C.c_int),('message',C.c_char_p)]

def errstr(glib,e):
    if not e:return 'no result/no GError'
    s=f'{e.contents.domain}:{e.contents.code}: '+e.contents.message.decode(errors='replace')
    glib.g_error_free(e); return s

addr=sys.argv[1]; seconds=float(sys.argv[2]) if len(sys.argv)>2 else 12.0; event=sys.argv[3] if len(sys.argv)>3 else 'object:state-changed'
gio=C.CDLL(ctypes.util.find_library('gio-2.0')); glib=C.CDLL(ctypes.util.find_library('glib-2.0')); gobj=C.CDLL(ctypes.util.find_library('gobject-2.0'))
ptr=C.c_void_p
gio.g_dbus_connection_new_for_address_sync.restype=ptr; gio.g_dbus_connection_new_for_address_sync.argtypes=[C.c_char_p,C.c_int,ptr,ptr,C.POINTER(C.POINTER(GError))]
gio.g_dbus_connection_call_sync.restype=ptr; gio.g_dbus_connection_call_sync.argtypes=[ptr,C.c_char_p,C.c_char_p,C.c_char_p,C.c_char_p,ptr,ptr,C.c_int,C.c_int,ptr,C.POINTER(C.POINTER(GError))]
gio.g_dbus_connection_get_unique_name.restype=C.c_char_p; gio.g_dbus_connection_get_unique_name.argtypes=[ptr]
gio.g_dbus_connection_close_sync.restype=C.c_int; gio.g_dbus_connection_close_sync.argtypes=[ptr,ptr,C.POINTER(C.POINTER(GError))]
glib.g_variant_new_string.restype=ptr; glib.g_variant_new_string.argtypes=[C.c_char_p]
glib.g_variant_new_strv.restype=ptr; glib.g_variant_new_strv.argtypes=[C.POINTER(C.c_char_p),C.c_ssize_t]
glib.g_variant_new_tuple.restype=ptr; glib.g_variant_new_tuple.argtypes=[C.POINTER(ptr),C.c_size_t]
glib.g_variant_ref_sink.restype=ptr; glib.g_variant_ref_sink.argtypes=[ptr]
glib.g_variant_unref.argtypes=[ptr]
glib.g_variant_get_type_string.restype=C.c_char_p; glib.g_variant_get_type_string.argtypes=[ptr]
glib.g_error_free.argtypes=[C.POINTER(GError)]
gobj.g_object_unref.argtypes=[ptr]
err=C.POINTER(GError)(); conn=gio.g_dbus_connection_new_for_address_sync(addr.encode(),9,None,None,C.byref(err))
if not conn: raise SystemExit('CONNECT '+errstr(glib,err))
unique=gio.g_dbus_connection_get_unique_name(conn).decode()
empty=(C.c_char_p*1)(); values=[glib.g_variant_new_string(event.encode()),glib.g_variant_new_strv(empty,0),glib.g_variant_new_string(b'')]
params=glib.g_variant_ref_sink(glib.g_variant_new_tuple((ptr*3)(*values),3))
err=C.POINTER(GError)(); ret=gio.g_dbus_connection_call_sync(conn,b'org.a11y.atspi.Registry',b'/org/a11y/atspi/registry',b'org.a11y.atspi.Registry',b'RegisterEvent',params,None,0,3000,None,C.byref(err));glib.g_variant_unref(params)
if not ret:
    gio.g_dbus_connection_close_sync(conn,None,C.byref(err));gobj.g_object_unref(conn);raise SystemExit('REGISTER '+errstr(glib,err))
rettype=glib.g_variant_get_type_string(ret).decode();glib.g_variant_unref(ret)
print(json.dumps({'registered':True,'unique_name':unique,'event':event,'return_type':rettype}),flush=True)
try: time.sleep(seconds)
finally:
    err=C.POINTER(GError)();gio.g_dbus_connection_close_sync(conn,None,C.byref(err));
    if err: glib.g_error_free(err)
    gobj.g_object_unref(conn)
