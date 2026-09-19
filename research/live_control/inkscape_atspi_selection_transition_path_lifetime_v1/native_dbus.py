"""Read-only typed D-Bus client using installed GIO through ctypes.
No service exports, injection, registry emulation or write methods are provided.
"""
import ctypes as C, ctypes.util

class GError(C.Structure):
    _fields_=[('domain',C.c_uint),('code',C.c_int),('message',C.c_char_p)]

class Client:
    def __init__(self,address):
        self.gio=C.CDLL(ctypes.util.find_library('gio-2.0'))
        self.glib=C.CDLL(ctypes.util.find_library('glib-2.0'))
        self.obj=C.CDLL(ctypes.util.find_library('gobject-2.0'))
        def f(lib,n,ret,args):
            fn=getattr(lib,n);fn.restype=ret;fn.argtypes=args;return fn
        ptr=C.c_void_p;errp=C.POINTER(C.POINTER(GError))
        self._connect=f(self.gio,'g_dbus_connection_new_for_address_sync',ptr,[C.c_char_p,C.c_int,ptr,ptr,errp])
        self._call=f(self.gio,'g_dbus_connection_call_sync',ptr,[ptr,C.c_char_p,C.c_char_p,C.c_char_p,C.c_char_p,ptr,ptr,C.c_int,C.c_int,ptr,errp])
        self._close=f(self.gio,'g_dbus_connection_close_sync',C.c_int,[ptr,ptr,errp])
        self._unobj=f(self.obj,'g_object_unref',None,[ptr])
        self._type=f(self.glib,'g_variant_get_type_string',C.c_char_p,[ptr])
        self._n=f(self.glib,'g_variant_n_children',C.c_size_t,[ptr])
        self._child=f(self.glib,'g_variant_get_child_value',ptr,[ptr,C.c_size_t])
        self._var=f(self.glib,'g_variant_get_variant',ptr,[ptr])
        self._un=f(self.glib,'g_variant_unref',None,[ptr])
        self._sink=f(self.glib,'g_variant_ref_sink',ptr,[ptr])
        self._str=f(self.glib,'g_variant_get_string',C.c_char_p,[ptr,C.POINTER(C.c_size_t)])
        self._snew=f(self.glib,'g_variant_new_string',ptr,[C.c_char_p])
        self._inew=f(self.glib,'g_variant_new_int32',ptr,[C.c_int32])
        self._tuple=f(self.glib,'g_variant_new_tuple',ptr,[C.POINTER(ptr),C.c_size_t])
        self._freeerr=f(self.glib,'g_error_free',None,[C.POINTER(GError)])
        self._scalar={}
        for sig,name,typ in [('b','boolean',C.c_int),('y','byte',C.c_ubyte),('n','int16',C.c_int16),('q','uint16',C.c_uint16),('i','int32',C.c_int32),('u','uint32',C.c_uint32),('x','int64',C.c_int64),('t','uint64',C.c_uint64),('h','handle',C.c_int32),('d','double',C.c_double)]:
            self._scalar[sig]=f(self.glib,'g_variant_get_'+name,typ,[ptr])
        err=C.POINTER(GError)();self.conn=self._connect(address.encode(),9,None,None,C.byref(err))
        if not self.conn:raise RuntimeError(self._error(err))
    def _error(self,e):
        if not e:return 'GIO call returned no result and no error'
        x=f'{e.contents.domain}:{e.contents.code}: '+e.contents.message.decode(errors='replace');self._freeerr(e);return x
    def _decode(self,p):
        sig=self._type(p).decode();c=sig[0]
        if c in 'sog':return self._str(p,None).decode(errors='strict')
        if c in self._scalar:
            v=self._scalar[c](p);return bool(v) if c=='b' else v
        if c=='v':
            q=self._var(p)
            try:return {'type':self._type(q).decode(),'data':self._decode(q)}
            finally:self._un(q)
        vals=[]
        for i in range(self._n(p)):
            q=self._child(p,i)
            try:vals.append(self._decode(q))
            finally:self._un(q)
        return dict(vals) if sig.startswith('a{') else vals
    def call(self,dest,path,iface,method,signature=None,vals=()):
        if (iface,method) not in {
            ('org.freedesktop.DBus','ListNames'),('org.freedesktop.DBus','GetConnectionUnixProcessID'),
            ('org.freedesktop.DBus.Properties','GetAll'),
            ('org.a11y.atspi.Accessible','GetChildren'),('org.a11y.atspi.Accessible','GetRoleName'),
            ('org.a11y.atspi.Accessible','GetInterfaces'),('org.a11y.atspi.Accessible','GetState'),
            ('org.a11y.atspi.Selection','GetSelectedChild'),('org.a11y.atspi.Text','GetText')}:
            raise ValueError('method is outside read-only allowlist')
        sig=signature or ''
        if len(sig)!=len(vals) or any(s not in 'si' for s in sig):raise ValueError('unsupported argument signature')
        args=[]
        for s,v in zip(sig,vals):
            if s=='s' and type(v) is str:args.append(self._snew(v.encode()))
            elif s=='i' and type(v) is int and -2**31<=v<2**31:args.append(self._inew(v))
            else:raise TypeError('invalid argument type')
        params=self._sink(self._tuple((C.c_void_p*len(args))(*args),len(args)))
        err=C.POINTER(GError)()
        try:p=self._call(self.conn,dest.encode(),path.encode(),iface.encode(),method.encode(),params,None,0,2000,None,C.byref(err))
        finally:self._un(params)
        if not p:return {'rc':1,'error':self._error(err),'response':None}
        try:
            t=self._type(p).decode();values=self._decode(p)
            return {'rc':0,'error':'','response':{'type':t[1:-1],'data':values}}
        finally:self._un(p)
    def close(self):
        if self.conn:
            err=C.POINTER(GError)();self._close(self.conn,None,C.byref(err))
            if err:self._freeerr(err)
            self._unobj(self.conn);self.conn=None
